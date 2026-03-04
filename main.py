from fastapi import FastAPI
from fastapi.security import HTTPBearer
from database import db
from routes import auth, messages

security = HTTPBearer()

app = FastAPI(
    title="ChatApp Backend",
    description="WhatsApp-like Chat API",
    version="1.0.0",
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(messages.router, prefix="/messages", tags=["Messages"])

@app.get("/")
def root():
    return {"status": "ChatApp backend is running!"}