import openai
import httpx
from fastapi import HTTPException
from datetime import datetime, timedelta
import asyncio

ALPHA_VANTAGE_API_KEY = 'xx'

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

async def fetch_stock_info(symbol: str = "AAPL"):  # Przykładowy symbol: Apple Inc. (AAPL)
    try:
        # Pobieranie danych akcji
        stock_data = await fetch_stock_data(symbol)

        # Ustal datę sprzed 30 dni
        thirty_days_ago = datetime.now() - timedelta(days=30)

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

        # Wyświetlanie informacji w konsoli
        print(f"Symbol: {symbol}")
        print(f"Analiza akcji: {stock_analysis}")
        print("Dane akcji z ostatnich 30 dni:")
        for price in stock_prices:
            print(f"Data: {price['date']}, Otwarcie: {price['open']}, Zamknięcie: {price['close']}")

        # Pobieranie artykułów o danej akcji
        articles = await fetch_alpha_vantage_news(symbol)

        print("Artykuły o akcji:")
        for article in articles:
            title = article['title']
            content = article['summary']
            date = article['published_at']  # Zakładam, że data jest w tym kluczu

            # Analiza treści artykułu
            status_value = await analyze_article_content(content)

            # Wyświetlanie artykułu w konsoli
            print(f"Tytuł: {title}")
            print(f"Data: {date}")
            print(f"Treść: {content}")
            print(f"Status: {status_value}")

        return stock_analysis
    except Exception as e:
        print(f"Błąd podczas pobierania informacji o akcji: {e}")
        return None

# Uruchomienie kodu
if __name__ == "__main__":
    asyncio.run(fetch_stock_info("AAPL"))  # Przykładowy symbol: AAPL
