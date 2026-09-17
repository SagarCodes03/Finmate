from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.finance import list_transactions
from app.schemas.finance import TransactionCreate, TransactionRead
from app.services.finance import create_transaction

router = APIRouter()


@router.get("", response_model=list[TransactionRead])
def get_transactions(account_id: int | None = None, db: Session = Depends(get_db)) -> list[TransactionRead]:
    return list_transactions(db, account_id)


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def add_transaction(payload: TransactionCreate, db: Session = Depends(get_db)) -> TransactionRead:
    return create_transaction(db, payload)
