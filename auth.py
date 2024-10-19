from datetime import timedelta, datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from starlette import status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError

from data.database import get_firestore_db

router = APIRouter(
    prefix='/auth',
    tags=['auth'],
)

SECRET_KEY = 'pG9Vt!3x5Tj&sP0q#wZ2Yk^bMf8nRxT@v7$Lp6Ud?Zj+WcCrE4XhQe1BfA5J9K'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')


class CreateUserRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(create_user_request: CreateUserRequest):
    db = get_firestore_db()  # Uzyskaj dostęp do Firestore
    users_ref = db.collection('users')

    # Sprawdzenie, czy użytkownik już istnieje
    existing_user = users_ref.where('username', '==', create_user_request.username).get()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")

    # Hashowanie hasła i tworzenie nowego użytkownika
    hashed_password = bcrypt_context.hash(create_user_request.password)
    new_user_data = {
        'username': create_user_request.username,
        'hashed_password': hashed_password
    }

    users_ref.add(new_user_data)  # Dodaj nowego użytkownika do Firestore
    return {'status': 'User created successfully'}


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    db = get_firestore_db()
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect username or password')

    token = create_access_token(user['username'], user['id'], timedelta(minutes=20))
    return {'access_token': token, 'token_type': 'bearer'}


def authenticate_user(username: str, password: str, db):
    users_ref = db.collection('users')
    user_docs = users_ref.where('username', '==', username).get()

    if not user_docs:
        return False

    user = user_docs[0].to_dict()
    if not bcrypt_context.verify(password, user['hashed_password']):
        return False

    user['id'] = user_docs[0].id  # Dodaj ID dokumentu do danych użytkownika
    return user


def create_access_token(username: str, user_id: str, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id}
    expires = datetime.utcnow() + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')

        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Could not validate user.")

        return {'username': username, 'id': user_id}

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user.')
