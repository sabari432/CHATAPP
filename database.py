from pymongo import MongoClient
from dotenv import load_dotenv
import os
import certifi
import ssl

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    tlsAllowInvalidCertificates=False
)

db = client.chatapp
users_collection = db["users"]
messages_collection = db["messages"]
groups_collection = db["groups"]

print("MongoDB Connected!")

