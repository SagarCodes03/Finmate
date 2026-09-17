from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Account, Transaction, User
from app.repositories.finance import get_user_by_email
from app.schemas.finance import AccountCreate, TransactionCreate, UserCreate


def create_user(db: Session, payload: UserCreate) -> User:
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")
    user = User(**payload.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_account(db: Session, payload: AccountCreate) -> Account:
    if not db.get(User, payload.user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    account = Account(**payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def create_transaction(db: Session, payload: TransactionCreate) -> Transaction:
    if not db.get(Account, payload.account_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    transaction = Transaction(**payload.model_dump())
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction
