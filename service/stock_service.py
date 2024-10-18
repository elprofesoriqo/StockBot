# stock_service.py

import openai
from sqlalchemy.orm import Session
import models


async def fetch_stock_info(symbol: str, db: Session):
    try:
        # Wysłanie zapytania do OpenAI
        response = await openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"Podaj analizę akcji {symbol}."}]
        )

        # Odbieranie odpowiedzi
        stock_analysis = response['choices'][0]['message']['content']

        # Sprawdzenie, czy akcja już istnieje
        stock = db.query(models.Stocks).filter(models.Stocks.symbol == symbol).first()

        if stock:
            # Jeśli akcja już istnieje, zaktualizuj analizę
            stock.analyse = stock_analysis
            db.commit()
            return stock_analysis
        else:
            # Jeśli akcja nie istnieje, stwórz nową
            new_stock = models.Stocks(symbol=symbol, name=symbol, curr_price=0, yesterday_price=0,
                                      analyse=stock_analysis)  # Uzupełnij inne pola zgodnie z potrzebami
            db.add(new_stock)
            db.commit()
            return stock_analysis
    except Exception as e:
        print(f"Błąd podczas pobierania informacji o akcji: {e}")
        return None
