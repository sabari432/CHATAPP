from fastapi import APIRouter, HTTPException
from models import SignupModel, LoginModel
from database import users_collection
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT config
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str):
    return pwd_context.verify(plain, hashed)

def create_token(data: dict):
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    data.update({"exp": expire})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


# ✅ SIGNUP
@router.post("/signup")
def signup(user: SignupModel):
    # Check if email already exists
    existing = users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password and save user
    hashed = hash_password(user.password)
    new_user = {
        "name": user.name,
        "email": user.email,
        "password": hashed,
        "created_at": datetime.utcnow()
    }
    result = users_collection.insert_one(new_user)

    # Create token
    token = create_token({"user_id": str(result.inserted_id)})

    return {
        "message": "Signup successful",
        "token": token,
        "user": {
            "id": str(result.inserted_id),
            "name": user.name,
            "email": user.email
        }
    }


# ✅ LOGIN
@router.post("/login")
def login(user: LoginModel):
    # Find user
    found = users_collection.find_one({"email": user.email})
    if not found:
        raise HTTPException(status_code=404, detail="User not found")

    # Check password
    if not verify_password(user.password, found["password"]):
        raise HTTPException(status_code=401, detail="Wrong password")

    # Create token
    token = create_token({"user_id": str(found["_id"])})

    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": str(found["_id"]),
            "name": found["name"],
            "email": found["email"]
        }
    }