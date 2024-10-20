import openai
from data.database import get_firestore_db
import httpx
from fastapi import HTTPException
from datetime import datetime, timedelta
from data.models import Comments

ALPHA_VANTAGE_API_KEY = '525RTDGM1B7TXKW5'
openai.api_key = "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"  # Zamień na swój klucz API


async def fetch_stock_data(symbol: str):
    url = f"https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Error fetching stock data")

        data = response.json()
        if "Error Message" in data:
            raise HTTPException(status_code=404, detail="Stock not found")

        return data["Time Series (Daily)"]


async def fetch_alpha_vantage_news(symbol: str):
    url = "https://www.alphavantage.co/query"
    params = {
        'function': 'NEWS',
        'tickers': symbol,
        'apikey': ALPHA_VANTAGE_API_KEY
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        if response.status_code == 200:
            return response.json()["feed"]
        else:
            raise HTTPException(status_code=response.status_code, detail="Error fetching news from Alpha Vantage")


async def analyze_article_content(content: str):
    try:
        response = await openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user",
                       "content": f"Na podstawie tego tekstu, określ, czy akcja będzie rosła czy malała: {content}. Odpowiedz w skali od -5 (spadek) do 5 (wzrost)."}]
        )
        status_value = response['choices'][0]['message']['content']
        return int(status_value)  # Zwróć wartość jako integer
    except Exception as e:
        print(f"Błąd podczas analizy artykułu: {e}")
        return 0  # Domyślna wartość w przypadku błędu


async def fetch_stock_info(symbol: str):
    try:
        # Pobieranie danych akcji
        stock_data = await fetch_stock_data(symbol)

        # Ustal datę sprzed 30 dni
        thirty_days_ago = datetime.now() - timedelta(days=30)

        # Przechowywanie danych do bazy
        db = get_firestore_db()
        stock_ref = db.collection('stocks').document(symbol)

        # Sprawdzanie czy dokument już istnieje
        stock_doc = stock_ref.get()
        stock_prices = []

        # Filtracja danych i zapis do listy
        for date, values in stock_data.items():
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            if date_obj >= thirty_days_ago:
                stock_prices.append({
                    "date": date,
                    "open": values['1. open'],
                    "high": values['2. high'],
                    "low": values['3. low'],
                    "close": values['4. close'],
                    "volume": values['5. volume']
                })

        # Wysłanie zapytania do OpenAI w celu analizy akcji
        response = await openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"Podaj analizę akcji {symbol}."}]
        )
        stock_analysis = response['choices'][0]['message']['content']

        # Zapis danych do Firestore
        if stock_doc.exists:
            stock_ref.update({
                'prices': stock_prices,
                'analyse': stock_analysis
            })
        else:
            stock_ref.set({
                'symbol': symbol,
                'name': symbol,
                'curr_price': stock_prices[-1]['close'] if stock_prices else 0,
                'yesterday_price': stock_prices[-2]['close'] if len(stock_prices) > 1 else 0,
                'prices': stock_prices,
                'analyse': stock_analysis
            })

        # Pobieranie artykułów o danej akcji
        articles = await fetch_alpha_vantage_news(symbol)

        # Zapis artykułów do bazy danych
        for article in articles:
            title = article['title']
            content = article['summary']
            date = article['published_at']  # Zakładam, że data jest w tym kluczu

            # Analiza treści artykułu
            status_value = await analyze_article_content(content)

            # Zapis do bazy danych
            comment = Comments(
                title=title,
                content=content,
                date=datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").isoformat(),
                status=status_value
            )
            db.add(comment)

        db.commit()  # Zapisz wszystkie zmiany

        return stock_analysis
    except Exception as e:
        print(f"Błąd podczas pobierania informacji o akcji: {e}")
        return None
