from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    email: str
    display_name: str = Field(min_length=1, max_length=120)


class UserRead(UserCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class AccountCreate(BaseModel):
    user_id: int
    name: str = Field(min_length=1, max_length=120)
    account_type: str = Field(default="checking", max_length=40)
    balance: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)


class AccountRead(AccountCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class TransactionCreate(BaseModel):
    account_id: int
    category_id: int | None = None
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    transaction_date: date
    note: str | None = Field(default=None, max_length=500)


class TransactionRead(TransactionCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
