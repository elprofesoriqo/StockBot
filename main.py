from email import message
from sqlite3 import Connection
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, status, Depends, HTTPException, WebSocket
from sqlalchemy.orm import Session
from typing import Annotated
import openai
from starlette.websockets import WebSocketDisconnect
import auth
import models
from database import engine, SessionLocal
from auth import get_current_user
import firebase_admin
from firebase_admin import credentials




app = FastAPI()
openai.api_key = "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"  # Zamień na swój klucz API




cred = credentials.Certificate("./serviceAccountKey.json")
firebase_admin.initialize_app(cred)




app.include_router(auth.router)

models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[SessionLocal, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[Connection] = []
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
async def read_user(user: user_dependency, db: db_dependency):
    return {'user': user}

@app.get("/stock/{symbol}", status_code=status.HTTP_200_OK)
async def stock_page(user: user_dependency, db: db_dependency):
    pass











@app.websocket("/chat/ws")
async def websocket_endpoint(websocket: WebSocket, user: user_dependency, db: db_dependency):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()

            chat_message = models.Chat(
                user_id=user["id"],
                title="Chat",
                comment=data
            )
            db.add(chat_message)
            db.commit()

            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"User {user['username']} wrote: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/chat", status_code=status.HTTP_200_OK)
async def get_chat_history(user: user_dependency, db: db_dependency):
    chat_history = db.query(models.Chat).order_by(models.Chat.id).all()

    return [
        {
            "user_id": chat_message.user_id,
            "username": user["username"],
            "message": chat_message.comment
        }
        for chat_message in chat_history
    ]