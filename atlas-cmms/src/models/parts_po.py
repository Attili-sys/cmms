"""SQLAlchemy models for group: parts_po."""

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


class Part(Base):
    __tablename__ = "part"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("part_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    additional_infos: Mapped[str | None] = mapped_column("additional_infos", Text, nullable=True)
    area: Mapped[str | None] = mapped_column("area", String(255), nullable=True)
    barcode: Mapped[str | None] = mapped_column("barcode", String(255), nullable=True)
    cost: Mapped[float] = mapped_column("cost", Float, nullable=False)
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    min_quantity: Mapped[float] = mapped_column("min_quantity", Float, nullable=False)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    non_stock: Mapped[bool] = mapped_column("non_stock", Boolean, nullable=False)
    quantity: Mapped[float] = mapped_column("quantity", Float, nullable=False)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    image_id: Mapped[int | None] = mapped_column("image_id", BigInteger, ForeignKey("file.id", ondelete="SET NULL"), nullable=True)
    category_id: Mapped[int | None] = mapped_column("category_id", BigInteger, ForeignKey("part_category.id", ondelete="CASCADE"), nullable=True)
    unit: Mapped[str | None] = mapped_column("unit", String(255), nullable=True)
    is_demo: Mapped[bool] = mapped_column("is_demo", Boolean, nullable=False)
    version: Mapped[int] = mapped_column("version", BigInteger, nullable=False)


class PartQuantity(Base):
    __tablename__ = "part_quantity"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("part_quantity_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    quantity: Mapped[float] = mapped_column("quantity", Float, nullable=False)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    part_id: Mapped[int] = mapped_column("part_id", BigInteger, ForeignKey("part.id", ondelete="CASCADE"), nullable=False)
    purchase_order_id: Mapped[int | None] = mapped_column("purchase_order_id", BigInteger, ForeignKey("purchase_order.id", ondelete="CASCADE"), nullable=True)
    work_order_id: Mapped[int | None] = mapped_column("work_order_id", BigInteger, ForeignKey("work_order.id", ondelete="CASCADE"), nullable=True)
    is_demo: Mapped[bool] = mapped_column("is_demo", Boolean, nullable=False)


class PartTransaction(Base):
    __tablename__ = "part_transaction"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("part_transaction_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    quantity: Mapped[float] = mapped_column("quantity", Float, nullable=False)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    part_id: Mapped[int] = mapped_column("part_id", BigInteger, ForeignKey("part.id", ondelete="CASCADE"), nullable=False)
    work_order_id: Mapped[int | None] = mapped_column("work_order_id", BigInteger, ForeignKey("work_order.id", ondelete="CASCADE"), nullable=True)
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)


class MultiParts(Base):
    __tablename__ = "multi_parts"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("multi_parts_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)


class PurchaseOrder(Base):
    __tablename__ = "purchase_order"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("purchase_order_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    additional_info_date: Mapped[datetime | None] = mapped_column("additional_info_date", DateTime, nullable=True)
    additional_info_notes: Mapped[str | None] = mapped_column("additional_info_notes", String(255), nullable=True)
    additional_info_requisitioned_name: Mapped[str | None] = mapped_column("additional_info_requisitioned_name", String(255), nullable=True)
    additional_info_shipping_order_category: Mapped[str | None] = mapped_column("additional_info_shipping_order_category", String(255), nullable=True)
    additional_info_term: Mapped[str | None] = mapped_column("additional_info_term", String(255), nullable=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    shipping_additional_detail: Mapped[str | None] = mapped_column("shipping_additional_detail", String(255), nullable=True)
    shipping_address: Mapped[str | None] = mapped_column("shipping_address", String(255), nullable=True)
    shipping_city: Mapped[str | None] = mapped_column("shipping_city", String(255), nullable=True)
    shipping_company_name: Mapped[str | None] = mapped_column("shipping_company_name", String(255), nullable=True)
    shipping_due_date: Mapped[datetime | None] = mapped_column("shipping_due_date", DateTime, nullable=True)
    shipping_fax: Mapped[str | None] = mapped_column("shipping_fax", String(255), nullable=True)
    shipping_phone: Mapped[str | None] = mapped_column("shipping_phone", String(255), nullable=True)
    shipping_ship_to_name: Mapped[str | None] = mapped_column("shipping_ship_to_name", String(255), nullable=True)
    shipping_state: Mapped[str | None] = mapped_column("shipping_state", String(255), nullable=True)
    shipping_zip_code: Mapped[str | None] = mapped_column("shipping_zip_code", String(255), nullable=True)
    status: Mapped[int | None] = mapped_column("status", SmallInteger, nullable=True)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[int | None] = mapped_column("category_id", BigInteger, ForeignKey("purchase_order_category.id", ondelete="SET NULL"), nullable=True)
    vendor_id: Mapped[int | None] = mapped_column("vendor_id", BigInteger, ForeignKey("vendor.id", ondelete="SET NULL"), nullable=True)
    is_demo: Mapped[bool] = mapped_column("is_demo", Boolean, nullable=False)


class AdditionalCost(Base):
    __tablename__ = "additional_cost"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("additional_cost_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    cost: Mapped[float] = mapped_column("cost", Float, nullable=False)
    date: Mapped[datetime | None] = mapped_column("date", DateTime, nullable=True)
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    include_to_total_cost: Mapped[bool] = mapped_column("include_to_total_cost", Boolean, nullable=False)
    category_id: Mapped[int | None] = mapped_column("category_id", BigInteger, ForeignKey("cost_category.id", ondelete="SET NULL"), nullable=True)
    assigned_to_id: Mapped[int | None] = mapped_column("assigned_to_id", BigInteger, ForeignKey("own_user.id", ondelete="SET NULL"), nullable=True)
    work_order_id: Mapped[int] = mapped_column("work_order_id", BigInteger, ForeignKey("work_order.id", ondelete="CASCADE"), nullable=False)
    is_demo: Mapped[bool] = mapped_column("is_demo", Boolean, nullable=False)


class Vendor(Base):
    __tablename__ = "vendor"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("vendor_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    address: Mapped[str | None] = mapped_column("address", String(255), nullable=True)
    email: Mapped[str | None] = mapped_column("email", String(255), nullable=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column("phone", String(255), nullable=True)
    website: Mapped[str | None] = mapped_column("website", String(255), nullable=True)
    company_name: Mapped[str] = mapped_column("company_name", String(255), nullable=False)
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    rate: Mapped[int] = mapped_column("rate", BigInteger, nullable=False)
    vendor_type: Mapped[str | None] = mapped_column("vendor_type", String(255), nullable=True)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    is_demo: Mapped[bool] = mapped_column("is_demo", Boolean, nullable=False)


class Customer(Base):
    __tablename__ = "customer"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("customer_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    address: Mapped[str | None] = mapped_column("address", String(255), nullable=True)
    email: Mapped[str | None] = mapped_column("email", String(255), nullable=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column("phone", String(255), nullable=True)
    website: Mapped[str | None] = mapped_column("website", String(255), nullable=True)
    billing_address: Mapped[str | None] = mapped_column("billing_address", String(255), nullable=True)
    billing_address2: Mapped[str | None] = mapped_column("billing_address2", String(255), nullable=True)
    billing_name: Mapped[str | None] = mapped_column("billing_name", String(255), nullable=True)
    customer_type: Mapped[str | None] = mapped_column("customer_type", String(255), nullable=True)
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    rate: Mapped[int] = mapped_column("rate", BigInteger, nullable=False)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    billing_currency_id: Mapped[int | None] = mapped_column("billing_currency_id", BigInteger, ForeignKey("currency.id", ondelete="SET NULL"), nullable=True)
    is_demo: Mapped[bool] = mapped_column("is_demo", Boolean, nullable=False)
