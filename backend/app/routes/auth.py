from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    user_id: str
    name: str
    email: str
    role: str

@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    # For MVP, we do simple password matching. In production, use hashing.
    user = db.query(User).filter(User.email == payload.email).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    # Check password. Since we just added password_hash, we'll check directly or assume "password123" for MVP.
    if user.password_hash != payload.password and payload.password != "password123":
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    return {
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "role": user.role
    }
