"""SQLAlchemy models for group: company."""

from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Sequence,
    SmallInteger,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.models._base import Base, utcnow
from src.models.enums import PlanFeatures


class Company(Base):
    __tablename__ = "company"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("company_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    address: Mapped[str | None] = mapped_column("address", String(255), nullable=True)
    city: Mapped[str | None] = mapped_column("city", String(255), nullable=True)
    email: Mapped[str | None] = mapped_column("email", String(255), nullable=True)
    employees_count: Mapped[int] = mapped_column("employees_count", Integer, nullable=False)
    name: Mapped[str | None] = mapped_column("name", String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column("phone", String(255), nullable=True)
    state: Mapped[str | None] = mapped_column("state", String(255), nullable=True)
    website: Mapped[str | None] = mapped_column("website", String(255), nullable=True)
    zip_code: Mapped[str | None] = mapped_column("zip_code", String(255), nullable=True)
    company_settings_id: Mapped[int | None] = mapped_column("company_settings_id", BigInteger, ForeignKey("company_settings.id", ondelete="CASCADE"), nullable=True)
    logo_id: Mapped[int | None] = mapped_column("logo_id", BigInteger, ForeignKey("file.id", ondelete="SET NULL"), nullable=True)
    subscription_id: Mapped[int | None] = mapped_column("subscription_id", BigInteger, ForeignKey("subscription.id", ondelete="SET NULL"), nullable=True)
    demo: Mapped[bool | None] = mapped_column("demo", Boolean, nullable=True)
    first_work_order_created: Mapped[bool] = mapped_column("first_work_order_created", Boolean, nullable=False)
    invited_users: Mapped[bool] = mapped_column("invited_users", Boolean, nullable=False)
    imported_assets: Mapped[bool] = mapped_column("imported_assets", Boolean, nullable=False)
    ldap_domain: Mapped[str | None] = mapped_column("ldap_domain", String(255), nullable=True)


class Subscription(Base):
    __tablename__ = "subscription"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("subscription_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    activated: Mapped[bool] = mapped_column("activated", Boolean, nullable=False)
    ends_on: Mapped[datetime | None] = mapped_column("ends_on", DateTime, nullable=True)
    monthly: Mapped[bool] = mapped_column("monthly", Boolean, nullable=False)
    starts_on: Mapped[datetime | None] = mapped_column("starts_on", DateTime, nullable=True)
    users_count: Mapped[int] = mapped_column("users_count", Integer, nullable=False)
    subscription_plan_id: Mapped[int] = mapped_column("subscription_plan_id", BigInteger, ForeignKey("subscription_plan.id", ondelete="CASCADE"), nullable=False)
    downgrade_needed: Mapped[bool] = mapped_column("downgrade_needed", Boolean, nullable=False)
    upgrade_needed: Mapped[bool] = mapped_column("upgrade_needed", Boolean, nullable=False)
    paddle_subscription_id: Mapped[str | None] = mapped_column("paddle_subscription_id", String(255), nullable=True)
    scheduled_change_date: Mapped[datetime | None] = mapped_column("scheduled_change_date", DateTime, nullable=True)
    scheduled_change_type: Mapped[int | None] = mapped_column("scheduled_change_type", SmallInteger, nullable=True)


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plan"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("subscription_plan_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    code: Mapped[str | None] = mapped_column("code", String(255), nullable=True)
    monthly_cost_per_user: Mapped[float] = mapped_column("monthly_cost_per_user", Float, nullable=False)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    yearly_cost_per_user: Mapped[float] = mapped_column("yearly_cost_per_user", Float, nullable=False)
    monthly_paddle_price_id: Mapped[str | None] = mapped_column("monthly_paddle_price_id", String(255), nullable=True)
    yearly_paddle_price_id: Mapped[str | None] = mapped_column("yearly_paddle_price_id", String(255), nullable=True)

    @property
    def features(self) -> set[PlanFeatures]:
        """Self-hosted policy: always return all PlanFeatures regardless of stored DB rows."""
        return set(PlanFeatures)


class SubscriptionChangeRequest(Base):
    __tablename__ = "subscription_change_request"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("subscription_change_request_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    code: Mapped[str] = mapped_column("code", String(255), nullable=False)
    monthly: Mapped[bool] = mapped_column("monthly", Boolean, nullable=False)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    users_count: Mapped[int] = mapped_column("users_count", Integer, nullable=False)


class Currency(Base):
    __tablename__ = "currency"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("currency_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    code: Mapped[str | None] = mapped_column("code", String(255), nullable=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
