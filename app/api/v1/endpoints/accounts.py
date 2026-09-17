from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.finance import list_accounts
from app.schemas.finance import AccountCreate, AccountRead
from app.services.finance import create_account

router = APIRouter()


@router.get("", response_model=list[AccountRead])
def get_accounts(user_id: int | None = None, db: Session = Depends(get_db)) -> list[AccountRead]:
    return list_accounts(db, user_id)


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def add_account(payload: AccountCreate, db: Session = Depends(get_db)) -> AccountRead:
    return create_account(db, payload)
