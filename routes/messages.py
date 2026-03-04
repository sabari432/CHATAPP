from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import messages_collection
from datetime import datetime
from jose import jwt, JWTError
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
security = HTTPBearer()
active_connections: dict = {}

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("user_id")
    except JWTError:
        return None


# ✅ SEND MESSAGE
@router.post("/send")
def send_message(
    payload: dict,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    user_id = verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    message = {
        "from_user": user_id,
        "to_user": payload.get("to_user"),
        "text": payload.get("text"),
        "timestamp": datetime.utcnow(),
        "is_read": False
    }
    result = messages_collection.insert_one(message)
    return {"message_id": str(result.inserted_id), "status": "Message sent"}


# ✅ GET MESSAGE HISTORY
@router.get("/history/{other_user_id}")
def get_messages(
    other_user_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    user_id = verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    msgs = messages_collection.find({
        "$or": [
            {"from_user": user_id, "to_user": other_user_id},
            {"from_user": other_user_id, "to_user": user_id}
        ]
    }).sort("timestamp", 1)

    result = []
    for m in msgs:
        result.append({
            "id": str(m["_id"]),
            "from_user": m["from_user"],
            "to_user": m["to_user"],
            "text": m["text"],
            "timestamp": str(m["timestamp"]),
            "is_read": m["is_read"]
        })
    return result


# ✅ WEBSOCKET
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    active_connections[user_id] = websocket
    print(f"User {user_id} connected")
    try:
        while True:
            data = await websocket.receive_json()
            to_user = data.get("to_user")
            text = data.get("text")
            message = {
                "from_user": user_id,
                "to_user": to_user,
                "text": text,
                "timestamp": datetime.utcnow(),
                "is_read": False
            }
            result = messages_collection.insert_one(message)
            if to_user in active_connections:
                await active_connections[to_user].send_json({
                    "from_user": user_id,
                    "text": text,
                    "message_id": str(result.inserted_id),
                    "timestamp": str(datetime.utcnow())
                })
    except WebSocketDisconnect:
        active_connections.pop(user_id, None)
        print(f"User {user_id} disconnected")