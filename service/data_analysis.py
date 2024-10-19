import pandas as pd
from fastapi import HTTPException
from data.database import get_firestore_db

async def generate_stock_excel(symbol: str):
    db = get_firestore_db()
    stock_ref = db.collection('stocks').document(symbol)
    comments_ref = db.collection('comments').document(symbol)

    stock_doc = stock_ref.get()




    if not stock_doc.exists:
        raise HTTPException(status_code=404, detail="Stock not found")

    stock_data = stock_doc.to_dict()
    prices = stock_data.get('prices', [])

    df = pd.DataFrame(prices)








    file_path = 'results.xlsx'
    df.to_excel(file_path, index=False)

    return file_path
