"""SQLAlchemy models for group: meters."""

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
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.models._base import Base, utcnow


class Meter(Base):
    __tablename__ = "meter"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("meter_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    unit: Mapped[str | None] = mapped_column("unit", String(255), nullable=True)
    update_frequency: Mapped[int] = mapped_column("update_frequency", Integer, nullable=False)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    asset_id: Mapped[int] = mapped_column("asset_id", BigInteger, ForeignKey("asset.id", ondelete="CASCADE"), nullable=False)
    image_id: Mapped[int | None] = mapped_column("image_id", BigInteger, ForeignKey("file.id", ondelete="SET NULL"), nullable=True)
    location_id: Mapped[int | None] = mapped_column("location_id", BigInteger, ForeignKey("location.id", ondelete="SET NULL"), nullable=True)
    meter_category_id: Mapped[int | None] = mapped_column("meter_category_id", BigInteger, ForeignKey("meter_category.id", ondelete="SET NULL"), nullable=True)
    is_demo: Mapped[bool] = mapped_column("is_demo", Boolean, nullable=False)


class Reading(Base):
    __tablename__ = "reading"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("reading_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    value: Mapped[float] = mapped_column("value", Float, nullable=False)
    meter_id: Mapped[int] = mapped_column("meter_id", BigInteger, ForeignKey("meter.id", ondelete="CASCADE"), nullable=False)


class WorkOrderMeterTrigger(Base):
    __tablename__ = "work_order_meter_trigger"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("work_order_meter_trigger_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
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
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    recurrent: Mapped[bool] = mapped_column("recurrent", Boolean, nullable=False)
    trigger_condition: Mapped[int] = mapped_column("trigger_condition", SmallInteger, nullable=False)
    value: Mapped[int] = mapped_column("value", Integer, nullable=False)
    wait_before: Mapped[int] = mapped_column("wait_before", Integer, nullable=False)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    asset_id: Mapped[int | None] = mapped_column("asset_id", BigInteger, ForeignKey("asset.id", ondelete="SET NULL"), nullable=True)
    category_id: Mapped[int | None] = mapped_column("category_id", BigInteger, ForeignKey("work_order_category.id", ondelete="SET NULL"), nullable=True)
    image_id: Mapped[int | None] = mapped_column("image_id", BigInteger, ForeignKey("file.id", ondelete="SET NULL"), nullable=True)
    location_id: Mapped[int | None] = mapped_column("location_id", BigInteger, ForeignKey("location.id", ondelete="SET NULL"), nullable=True)
    primary_user_id: Mapped[int | None] = mapped_column("primary_user_id", BigInteger, ForeignKey("own_user.id", ondelete="SET NULL"), nullable=True)
    team_id: Mapped[int | None] = mapped_column("team_id", BigInteger, ForeignKey("team.id", ondelete="SET NULL"), nullable=True)
    meter_id: Mapped[int] = mapped_column("meter_id", BigInteger, ForeignKey("meter.id", ondelete="CASCADE"), nullable=False)
    estimated_start_date: Mapped[datetime | None] = mapped_column("estimated_start_date", DateTime, nullable=True)
