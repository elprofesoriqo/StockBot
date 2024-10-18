# main.py

from fastapi import FastAPI, status, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated

import auth
import models
from database import SessionLocal
from auth import get_current_user
from stock_service import fetch_stock_info  # Importuj nową funkcję

app = FastAPI()

# Ustawienie OpenAI API key
openai.api_key = "YOUR_API_KEY"  # Zamień na swój klucz API

# Inicjalizacja Firebase (już wcześniej zaimplementowana)

app.include_router(auth.router)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[SessionLocal, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@app.get("/stock/{symbol}", status_code=status.HTTP_200_OK)
async def stock_page(symbol: str, user: user_dependency, db: db_dependency):
    stock_info = await fetch_stock_info(symbol, db)
    if stock_info:
        return {"symbol": symbol, "analysis": stock_info}
    raise HTTPException(status_code=404, detail="Nie znaleziono informacji o akcji.")
