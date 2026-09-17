from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Account, Transaction, User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def list_accounts(db: Session, user_id: int | None = None) -> list[Account]:
    statement = select(Account).order_by(Account.id)
    if user_id is not None:
        statement = statement.where(Account.user_id == user_id)
    return list(db.scalars(statement))


def list_transactions(db: Session, account_id: int | None = None) -> list[Transaction]:
    statement = select(Transaction).order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
    if account_id is not None:
        statement = statement.where(Transaction.account_id == account_id)
    return list(db.scalars(statement))
