"""SQLAlchemy models for group: requests."""

from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Sequence,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.models._base import Base, utcnow


class Request(Base):
    __tablename__ = "request"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("request_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column("due_date", DateTime, nullable=True)
    estimated_duration: Mapped[float] = mapped_column("estimated_duration", Float, nullable=False)
    priority: Mapped[int | None] = mapped_column("priority", SmallInteger, nullable=True)
    required_signature: Mapped[bool] = mapped_column("required_signature", Boolean, nullable=False)
    title: Mapped[str] = mapped_column("title", String(255), nullable=False)
    cancelled: Mapped[bool] = mapped_column("cancelled", Boolean, nullable=False)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    asset_id: Mapped[int | None] = mapped_column("asset_id", BigInteger, ForeignKey("asset.id", ondelete="SET NULL"), nullable=True)
    category_id: Mapped[int | None] = mapped_column("category_id", BigInteger, ForeignKey("work_order_category.id", ondelete="SET NULL"), nullable=True)
    image_id: Mapped[int | None] = mapped_column("image_id", BigInteger, ForeignKey("file.id", ondelete="SET NULL"), nullable=True)
    location_id: Mapped[int | None] = mapped_column("location_id", BigInteger, ForeignKey("location.id", ondelete="SET NULL"), nullable=True)
    primary_user_id: Mapped[int | None] = mapped_column("primary_user_id", BigInteger, ForeignKey("own_user.id", ondelete="SET NULL"), nullable=True)
    team_id: Mapped[int | None] = mapped_column("team_id", BigInteger, ForeignKey("team.id", ondelete="SET NULL"), nullable=True)
    work_order_id: Mapped[int | None] = mapped_column("work_order_id", BigInteger, ForeignKey("work_order.id", ondelete="SET NULL"), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column("cancellation_reason", Text, nullable=True)
    estimated_start_date: Mapped[datetime | None] = mapped_column("estimated_start_date", DateTime, nullable=True)
    audio_description_id: Mapped[int | None] = mapped_column("audio_description_id", BigInteger, ForeignKey("file.id", ondelete="CASCADE"), nullable=True)
    custom_id: Mapped[str | None] = mapped_column("custom_id", String(255), nullable=True)
    is_demo: Mapped[bool] = mapped_column("is_demo", Boolean, nullable=False)
    request_portal_id: Mapped[int | None] = mapped_column("request_portal_id", BigInteger, ForeignKey("request_portal.id", ondelete="SET NULL"), nullable=True)
    contact: Mapped[str | None] = mapped_column("contact", String(255), nullable=True)


class RequestPortal(Base):
    __tablename__ = "request_portal"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("request_portal_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id"), nullable=False)
    title: Mapped[str] = mapped_column("title", String(255), nullable=False)
    welcome_message: Mapped[str | None] = mapped_column("welcome_message", Text, nullable=True)
    uuid: Mapped[str] = mapped_column("uuid", String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)


class RequestPortalField(Base):
    __tablename__ = "request_portal_field"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("request_portal_field_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id"), nullable=False)
    type: Mapped[str] = mapped_column("type", String(255), nullable=False)
    location_id: Mapped[int | None] = mapped_column("location_id", BigInteger, ForeignKey("location.id"), nullable=True)
    asset_id: Mapped[int | None] = mapped_column("asset_id", BigInteger, ForeignKey("asset.id"), nullable=True)
    required: Mapped[bool] = mapped_column("required", Boolean, nullable=False)
    request_portal_id: Mapped[int] = mapped_column("request_portal_id", BigInteger, ForeignKey("request_portal.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
