"""SQLite models for clearly labeled simulated FinMate demo context."""

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DemoCustomer(Base):
    __tablename__ = "demo_customers"

    customer_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True)
    default_goal: Mapped[str] = mapped_column(String(500))
    default_requested_amount: Mapped[int] = mapped_column(Integer)

    business_profile: Mapped["BusinessProfile"] = relationship(back_populates="customer", cascade="all, delete-orphan", uselist=False)
    financial_profile: Mapped["FinancialProfile"] = relationship(back_populates="customer", cascade="all, delete-orphan", uselist=False)
    credit_profile: Mapped["CreditProfile"] = relationship(back_populates="customer", cascade="all, delete-orphan", uselist=False)


class BusinessProfile(Base):
    __tablename__ = "business_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("demo_customers.customer_id"), unique=True, index=True)
    business_type: Mapped[str] = mapped_column(String(100))
    business_tenure_years: Mapped[int] = mapped_column(Integer)
    customer_identity_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    business_context_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    required_documents_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    existing_customer_relationship: Mapped[bool] = mapped_column(Boolean, default=False)
    recovery_allowed: Mapped[bool] = mapped_column(Boolean, default=True)

    customer: Mapped[DemoCustomer] = relationship(back_populates="business_profile")


class FinancialProfile(Base):
    __tablename__ = "financial_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("demo_customers.customer_id"), unique=True, index=True)
    monthly_revenue: Mapped[float] = mapped_column(Float)
    annual_revenue: Mapped[float] = mapped_column(Float)
    existing_obligations: Mapped[float] = mapped_column(Float)
    dti_n: Mapped[float] = mapped_column(Float)
    purpose: Mapped[str] = mapped_column(String(100))
    account_activity_summary: Mapped[str] = mapped_column(String(200))

    customer: Mapped[DemoCustomer] = relationship(back_populates="financial_profile")


class CreditProfile(Base):
    __tablename__ = "credit_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("demo_customers.customer_id"), unique=True, index=True)
    fico_n: Mapped[float] = mapped_column(Float)
    emp_length: Mapped[str] = mapped_column(String(40))
    home_ownership_n: Mapped[str] = mapped_column(String(40))
    credit_summary: Mapped[str] = mapped_column(String(200))

    customer: Mapped[DemoCustomer] = relationship(back_populates="credit_profile")
