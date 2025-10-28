from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.api.schemas.user_schema import UserCreate, UserLogin, UserResponse
from src.api.database.connection import get_auth_db
from src.api.services.auth_service import register_user, login_user
from src.api.utils.jwt_utils import verify_token
from src.api.models.user_model import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_auth_db)):
    return register_user(db, user.username, user.email, user.password)

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_auth_db)):
    return login_user(db, user.email, user.password)

@router.get("/me")
def get_me(token_data: dict = Depends(verify_token), db: Session = Depends(get_auth_db)):
    user = db.query(User).filter(User.email == token_data["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_admin": getattr(user, 'is_admin', False)  # Handle if is_admin doesn't exist
    }
