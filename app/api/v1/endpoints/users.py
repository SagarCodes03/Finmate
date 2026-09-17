from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.finance import UserCreate, UserRead
from app.services.finance import create_user

router = APIRouter()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    return create_user(db, payload)
