"""SQLAlchemy models for group: files_custom."""

from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Sequence,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.models._base import Base, utcnow


class File(Base):
    __tablename__ = "file"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("file_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    type: Mapped[int | None] = mapped_column("type", SmallInteger, nullable=True)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    task_id: Mapped[int | None] = mapped_column("task_id", BigInteger, ForeignKey("task.id", ondelete="CASCADE"), nullable=True)
    hidden: Mapped[bool] = mapped_column("hidden", Boolean, nullable=False)
    path: Mapped[str] = mapped_column("path", Text, nullable=False)
    thumbnail_path: Mapped[str | None] = mapped_column("thumbnail_path", String(255), nullable=True)


class CustomField(Base):
    __tablename__ = "custom_field"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("custom_field_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    label: Mapped[str] = mapped_column("label", String(255), nullable=False)
    field_type: Mapped[str] = mapped_column("field_type", String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column("entity_type", String(255), nullable=False)
    required: Mapped[bool] = mapped_column("required", Boolean, nullable=False)
    copy_on_repeat: Mapped[bool] = mapped_column("copy_on_repeat", Boolean, nullable=False)
    company_settings_id: Mapped[int] = mapped_column("company_settings_id", BigInteger, ForeignKey("company_settings.id", ondelete="CASCADE"), nullable=False)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    field_order: Mapped[int] = mapped_column("field_order", Integer, nullable=False)


class CustomFieldValue(Base):
    __tablename__ = "custom_field_value"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("custom_field_value_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    custom_field_id: Mapped[int] = mapped_column("custom_field_id", BigInteger, ForeignKey("custom_field.id", ondelete="CASCADE"), nullable=False)
    value: Mapped[str | None] = mapped_column("value", Text, nullable=True)
    work_order_id: Mapped[int | None] = mapped_column("work_order_id", BigInteger, ForeignKey("work_order.id", ondelete="CASCADE"), nullable=True)
    asset_id: Mapped[int | None] = mapped_column("asset_id", BigInteger, ForeignKey("asset.id", ondelete="CASCADE"), nullable=True)
    location_id: Mapped[int | None] = mapped_column("location_id", BigInteger, ForeignKey("location.id", ondelete="CASCADE"), nullable=True)
    customer_id: Mapped[int | None] = mapped_column("customer_id", BigInteger, ForeignKey("customer.id", ondelete="CASCADE"), nullable=True)
    vendor_id: Mapped[int | None] = mapped_column("vendor_id", BigInteger, ForeignKey("vendor.id", ondelete="CASCADE"), nullable=True)
    part_id: Mapped[int | None] = mapped_column("part_id", BigInteger, ForeignKey("part.id", ondelete="CASCADE"), nullable=True)
    meter_id: Mapped[int | None] = mapped_column("meter_id", BigInteger, ForeignKey("meter.id", ondelete="CASCADE"), nullable=True)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    preventive_maintenance_id: Mapped[int | None] = mapped_column("preventive_maintenance_id", BigInteger, ForeignKey("preventive_maintenance.id", ondelete="CASCADE"), nullable=True)
    request_id: Mapped[int | None] = mapped_column("request_id", BigInteger, ForeignKey("request.id", ondelete="CASCADE"), nullable=True)
    work_order_meter_trigger_id: Mapped[int | None] = mapped_column("work_order_meter_trigger_id", BigInteger, ForeignKey("work_order_meter_trigger.id", ondelete="CASCADE"), nullable=True)


class Notification(Base):
    __tablename__ = "notification"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("notification_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    message: Mapped[str] = mapped_column("message", String(255), nullable=False)
    notification_type: Mapped[int | None] = mapped_column("notification_type", SmallInteger, nullable=True)
    resource_id: Mapped[int | None] = mapped_column("resource_id", BigInteger, nullable=True)
    seen: Mapped[bool] = mapped_column("seen", Boolean, nullable=False)
    user_id: Mapped[int | None] = mapped_column("user_id", BigInteger, ForeignKey("own_user.id", ondelete="SET NULL"), nullable=True)
