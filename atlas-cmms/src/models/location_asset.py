"""SQLAlchemy models for group: location_asset."""

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


class Location(Base):
    __tablename__ = "location"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("location_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    address: Mapped[str | None] = mapped_column("address", String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column("latitude", Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column("longitude", Float, nullable=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    image_id: Mapped[int | None] = mapped_column("image_id", BigInteger, ForeignKey("file.id", ondelete="SET NULL"), nullable=True)
    parent_location_id: Mapped[int | None] = mapped_column("parent_location_id", BigInteger, ForeignKey("location.id", ondelete="CASCADE"), nullable=True)
    custom_id: Mapped[str | None] = mapped_column("custom_id", String(255), nullable=True)
    is_demo: Mapped[bool] = mapped_column("is_demo", Boolean, nullable=False)


class Asset(Base):
    __tablename__ = "asset"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("asset_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    acquisition_cost: Mapped[float | None] = mapped_column("acquisition_cost", Float, nullable=True)
    additional_infos: Mapped[str | None] = mapped_column("additional_infos", Text, nullable=True)
    archived: Mapped[bool] = mapped_column("archived", Boolean, nullable=False)
    area: Mapped[str | None] = mapped_column("area", String(255), nullable=True)
    bar_code: Mapped[str | None] = mapped_column("bar_code", String(255), nullable=True)
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    in_service_date: Mapped[datetime | None] = mapped_column("in_service_date", DateTime, nullable=True)
    model: Mapped[str | None] = mapped_column("model", String(255), nullable=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    serial_number: Mapped[str | None] = mapped_column("serial_number", String(255), nullable=True)
    status: Mapped[int | None] = mapped_column("status", SmallInteger, nullable=True)
    warranty_expiration_date: Mapped[datetime | None] = mapped_column("warranty_expiration_date", DateTime, nullable=True)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[int | None] = mapped_column("category_id", BigInteger, ForeignKey("asset_category.id", ondelete="SET NULL"), nullable=True)
    deprecation_id: Mapped[int | None] = mapped_column("deprecation_id", BigInteger, ForeignKey("deprecation.id", ondelete="SET NULL"), nullable=True)
    image_id: Mapped[int | None] = mapped_column("image_id", BigInteger, ForeignKey("file.id", ondelete="SET NULL"), nullable=True)
    location_id: Mapped[int | None] = mapped_column("location_id", BigInteger, ForeignKey("location.id", ondelete="SET NULL"), nullable=True)
    parent_asset_id: Mapped[int | None] = mapped_column("parent_asset_id", BigInteger, ForeignKey("asset.id", ondelete="CASCADE"), nullable=True)
    primary_user_id: Mapped[int | None] = mapped_column("primary_user_id", BigInteger, ForeignKey("own_user.id", ondelete="SET NULL"), nullable=True)
    nfc_id: Mapped[str | None] = mapped_column("nfc_id", String(255), nullable=True)
    power: Mapped[str | None] = mapped_column("power", String(255), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column("manufacturer", String(255), nullable=True)
    custom_id: Mapped[str | None] = mapped_column("custom_id", String(255), nullable=True)
    is_demo: Mapped[bool] = mapped_column("is_demo", Boolean, nullable=False)


class AssetDowntime(Base):
    __tablename__ = "asset_downtime"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("asset_downtime_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    duration: Mapped[int] = mapped_column("duration", BigInteger, nullable=False)
    starts_on: Mapped[datetime | None] = mapped_column("starts_on", DateTime, nullable=True)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    asset_id: Mapped[int] = mapped_column("asset_id", BigInteger, ForeignKey("asset.id", ondelete="CASCADE"), nullable=False)


class Deprecation(Base):
    __tablename__ = "deprecation"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("deprecation_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    current_value: Mapped[int] = mapped_column("current_value", BigInteger, nullable=False)
    purchase_date: Mapped[datetime | None] = mapped_column("purchase_date", DateTime, nullable=True)
    purchase_price: Mapped[int] = mapped_column("purchase_price", BigInteger, nullable=False)
    rate: Mapped[int] = mapped_column("rate", Integer, nullable=False)
    residual_value: Mapped[str | None] = mapped_column("residual_value", String(255), nullable=True)
    usefullife: Mapped[str | None] = mapped_column("usefullife", String(255), nullable=True)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)


class FloorPlan(Base):
    __tablename__ = "floor_plan"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("floor_plan_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    area: Mapped[int] = mapped_column("area", BigInteger, nullable=False)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    image_id: Mapped[int | None] = mapped_column("image_id", BigInteger, ForeignKey("file.id", ondelete="SET NULL"), nullable=True)
    location_id: Mapped[int] = mapped_column("location_id", BigInteger, ForeignKey("location.id", ondelete="CASCADE"), nullable=False)
