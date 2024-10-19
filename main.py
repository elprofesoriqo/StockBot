from http.client import HTTPException

import openai
from aiohttp.web_fileresponse import FileResponse
from fastapi import FastAPI, status, Depends, WebSocket
from typing import Annotated
from starlette.websockets import WebSocketDisconnect
import auth
from auth import get_current_user
import firebase_admin
from firebase_admin import credentials, firestore

from service.data_analysis import generate_stock_excel
from service.stock_service import fetch_stock_info

# Inicjalizacja FastAPI
app = FastAPI()


cred = credentials.Certificate("server/serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()  # Inicjalizacja klienta Firestore

app.include_router(auth.router)

user_dependency = Annotated[dict, Depends(get_current_user)]

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.get("/", status_code=status.HTTP_200_OK)
async def read_user(user: user_dependency):
    return {'user': user}

@app.websocket("/chat/ws")
async def websocket_endpoint(websocket: WebSocket, user: user_dependency):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()

            # Zapisanie wiadomości do Firestore
            chat_ref = db.collection('chats').document()  # Tworzenie nowego dokumentu w kolekcji "chats"
            chat_ref.set({
                'user_id': user["id"],
                'username': user["username"],
                'message': data
            })

            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"User {user['username']} wrote: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/chat", status_code=status.HTTP_200_OK)
async def get_chat_history(user: user_dependency):
    # Pobieranie wiadomości z Firestore
    chats_ref = db.collection('chats')
    chat_history = chats_ref.order_by('message').stream()

    return [
        {
            "user_id": chat.get("user_id"),
            "username": chat.get("username"),
            "message": chat.get("message")
        }
        for chat in chat_history
    ]

@app.get("/stock/{symbol}", status_code=status.HTTP_200_OK)
async def stock_page(symbol: str, user: user_dependency):
    stock_analysis = await fetch_stock_info(symbol)
    return {
        "status": "Stock data updated",
        "symbol": symbol,
        "analysis": stock_analysis  # Możesz zwrócić analizę akcji, jeśli chcesz
    }


@app.get("/stock/{symbol}/download")
async def download_file(symbol: str):
    try:
        file_path = await generate_stock_excel(symbol)  # Wywołaj funkcję
        return FileResponse(file_path, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename='results.xlsx')
    except HTTPException as e:
        raise e  # Przekazuj wyjątek do FastAPI
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))