import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("server/serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

def get_firestore_db():
    return db
