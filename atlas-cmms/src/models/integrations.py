"""SQLAlchemy models for group: integrations."""

from datetime import date, datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Sequence,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.models._base import Base, utcnow


class ApiKey(Base):
    __tablename__ = "api_key"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("api_key_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    label: Mapped[str] = mapped_column("label", String(255), nullable=False)
    code: Mapped[str] = mapped_column("code", String(500), nullable=False)
    user_id: Mapped[int] = mapped_column("user_id", BigInteger, ForeignKey("own_user.id", ondelete="CASCADE"), nullable=False)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    last_used: Mapped[datetime | None] = mapped_column("last_used", DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column("expires_at", DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column("revoked_at", DateTime, nullable=True)


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoint"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("webhook_endpoint_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    url: Mapped[str] = mapped_column("url", String(255), nullable=False)
    secret: Mapped[str] = mapped_column("secret", String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column("enabled", Boolean, nullable=False)
    serialize: Mapped[bool | None] = mapped_column("serialize", Boolean, nullable=True)
    event: Mapped[str] = mapped_column("event", String(255), nullable=False)
    last_triggered_at: Mapped[datetime | None] = mapped_column("last_triggered_at", DateTime, nullable=True)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    approved: Mapped[bool | None] = mapped_column("approved", Boolean, nullable=True)


class KeygenRequestTracker(Base):
    __tablename__ = "keygen_request_tracker"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, nullable=False)
    request_date: Mapped[date] = mapped_column("request_date", Date, nullable=False)
    request_count: Mapped[int] = mapped_column("request_count", Integer, nullable=False)
