"""SQLAlchemy models for group: categories."""

from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Sequence,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.models._base import Base, utcnow


class AssetCategory(Base):
    __tablename__ = "asset_category"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("asset_category_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    company_settings_id: Mapped[int] = mapped_column("company_settings_id", BigInteger, ForeignKey("company_settings.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column("is_demo", Boolean, nullable=False)


class MeterCategory(Base):
    __tablename__ = "meter_category"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("meter_category_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    company_settings_id: Mapped[int] = mapped_column("company_settings_id", BigInteger, ForeignKey("company_settings.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column("is_demo", Boolean, nullable=False)


class PartCategory(Base):
    __tablename__ = "part_category"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("part_category_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    company_settings_id: Mapped[int] = mapped_column("company_settings_id", BigInteger, ForeignKey("company_settings.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column("is_demo", Boolean, nullable=False)


class PurchaseOrderCategory(Base):
    __tablename__ = "purchase_order_category"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("purchase_order_category_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    company_settings_id: Mapped[int] = mapped_column("company_settings_id", BigInteger, ForeignKey("company_settings.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column("is_demo", Boolean, nullable=False)


class WorkOrderCategory(Base):
    __tablename__ = "work_order_category"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("work_order_category_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    company_settings_id: Mapped[int] = mapped_column("company_settings_id", BigInteger, ForeignKey("company_settings.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column("is_demo", Boolean, nullable=False)


class CostCategory(Base):
    __tablename__ = "cost_category"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("cost_category_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    company_settings_id: Mapped[int] = mapped_column("company_settings_id", BigInteger, ForeignKey("company_settings.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column("is_demo", Boolean, nullable=False)


class TimeCategory(Base):
    __tablename__ = "time_category"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("time_category_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    company_settings_id: Mapped[int] = mapped_column("company_settings_id", BigInteger, ForeignKey("company_settings.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column("is_demo", Boolean, nullable=False)
