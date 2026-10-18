"""SQLAlchemy models for group: tasks."""

from datetime import datetime
from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Sequence,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.models._base import Base, utcnow


class Task(Base):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("task_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    notes: Mapped[str | None] = mapped_column("notes", String(255), nullable=True)
    value: Mapped[str | None] = mapped_column("value", String(255), nullable=True)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    task_base_id: Mapped[int] = mapped_column("task_base_id", BigInteger, ForeignKey("task_base.id", ondelete="CASCADE"), nullable=False)
    work_order_id: Mapped[int | None] = mapped_column("work_order_id", BigInteger, ForeignKey("work_order.id", ondelete="CASCADE"), nullable=True)
    preventive_maintenance_id: Mapped[int | None] = mapped_column("preventive_maintenance_id", BigInteger, ForeignKey("preventive_maintenance.id", ondelete="CASCADE"), nullable=True)


class TaskBase(Base):
    __tablename__ = "task_base"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("task_base_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    label: Mapped[str] = mapped_column("label", String(255), nullable=False)
    task_type: Mapped[int | None] = mapped_column("task_type", SmallInteger, nullable=True)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    asset_id: Mapped[int | None] = mapped_column("asset_id", BigInteger, ForeignKey("asset.id", ondelete="CASCADE"), nullable=True)
    meter_id: Mapped[int | None] = mapped_column("meter_id", BigInteger, ForeignKey("meter.id", ondelete="CASCADE"), nullable=True)
    user_id: Mapped[int | None] = mapped_column("user_id", BigInteger, ForeignKey("own_user.id", ondelete="SET NULL"), nullable=True)


class TaskOption(Base):
    __tablename__ = "task_option"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("task_option_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    label: Mapped[str | None] = mapped_column("label", String(255), nullable=True)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    task_base_id: Mapped[int | None] = mapped_column("task_base_id", BigInteger, ForeignKey("task_base.id", ondelete="SET NULL"), nullable=True)


class Checklist(Base):
    __tablename__ = "checklist"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("checklist_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    category: Mapped[str | None] = mapped_column("category", String(255), nullable=True)
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    company_settings_id: Mapped[int] = mapped_column("company_settings_id", BigInteger, ForeignKey("company_settings.id", ondelete="CASCADE"), nullable=False)
