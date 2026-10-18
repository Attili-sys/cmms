"""SQLAlchemy models for group: settings."""

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
)
from sqlalchemy.orm import Mapped, mapped_column

from src.models._base import Base, utcnow


class CompanySettings(Base):
    __tablename__ = "company_settings"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("company_settings_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    work_order_request_configuration_id: Mapped[int | None] = mapped_column("work_order_request_configuration_id", BigInteger, ForeignKey("work_order_request_configuration.id", ondelete="SET NULL"), nullable=True)
    company_id: Mapped[int | None] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=True)
    general_preferences_id: Mapped[int | None] = mapped_column("general_preferences_id", BigInteger, ForeignKey("general_preferences.id", ondelete="SET NULL"), nullable=True)
    work_order_configuration_id: Mapped[int | None] = mapped_column("work_order_configuration_id", BigInteger, ForeignKey("work_order_configuration.id", ondelete="SET NULL"), nullable=True)
    ui_configuration_id: Mapped[int | None] = mapped_column("ui_configuration_id", BigInteger, ForeignKey("ui_configuration.id", ondelete="CASCADE"), nullable=True)


class GeneralPreferences(Base):
    __tablename__ = "general_preferences"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("general_preferences_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    ask_feed_back_onwoclosed: Mapped[bool] = mapped_column("ask_feed_back_onwoclosed", Boolean, nullable=False)
    auto_assign_requests: Mapped[bool] = mapped_column("auto_assign_requests", Boolean, nullable=False)
    auto_assign_work_orders: Mapped[bool] = mapped_column("auto_assign_work_orders", Boolean, nullable=False)
    business_type: Mapped[int | None] = mapped_column("business_type", SmallInteger, nullable=True)
    date_format: Mapped[int | None] = mapped_column("date_format", SmallInteger, nullable=True)
    disable_closed_work_orders_notif: Mapped[bool] = mapped_column("disable_closed_work_orders_notif", Boolean, nullable=False)
    labor_cost_in_total_cost: Mapped[bool] = mapped_column("labor_cost_in_total_cost", Boolean, nullable=False)
    language: Mapped[int | None] = mapped_column("language", SmallInteger, nullable=True)
    time_zone: Mapped[str] = mapped_column("time_zone", String(255), nullable=False)
    wo_update_for_requesters: Mapped[bool] = mapped_column("wo_update_for_requesters", Boolean, nullable=False)
    company_settings_id: Mapped[int | None] = mapped_column("company_settings_id", BigInteger, ForeignKey("company_settings.id", ondelete="CASCADE"), nullable=True)
    currency_id: Mapped[int | None] = mapped_column("currency_id", BigInteger, ForeignKey("currency.id", ondelete="SET NULL"), nullable=True)
    simplified_work_order: Mapped[bool] = mapped_column("simplified_work_order", Boolean, nullable=False)
    days_before_prev_maint_notification: Mapped[int] = mapped_column("days_before_prev_maint_notification", Integer, nullable=False)
    csv_separator: Mapped[str | None] = mapped_column("csv_separator", String(255), nullable=True)
    auto_generate_asset_barcode: Mapped[bool | None] = mapped_column("auto_generate_asset_barcode", Boolean, nullable=True)
    color: Mapped[str | None] = mapped_column("color", String(255), nullable=True)


class WorkOrderConfiguration(Base):
    __tablename__ = "work_order_configuration"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("work_order_configuration_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    company_settings_id: Mapped[int | None] = mapped_column("company_settings_id", BigInteger, ForeignKey("company_settings.id", ondelete="CASCADE"), nullable=True)


class WorkOrderRequestConfiguration(Base):
    __tablename__ = "work_order_request_configuration"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("work_order_request_configuration_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    company_settings_id: Mapped[int | None] = mapped_column("company_settings_id", BigInteger, ForeignKey("company_settings.id", ondelete="CASCADE"), nullable=True)


class FieldConfiguration(Base):
    __tablename__ = "field_configuration"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("field_configuration_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    field_name: Mapped[str] = mapped_column("field_name", String(255), nullable=False)
    field_type: Mapped[int | None] = mapped_column("field_type", SmallInteger, nullable=True)
    work_order_configuration_id: Mapped[int | None] = mapped_column("work_order_configuration_id", BigInteger, ForeignKey("work_order_configuration.id", ondelete="SET NULL"), nullable=True)
    work_order_request_configuration_id: Mapped[int | None] = mapped_column("work_order_request_configuration_id", BigInteger, ForeignKey("work_order_request_configuration.id", ondelete="SET NULL"), nullable=True)


class UiConfiguration(Base):
    __tablename__ = "ui_configuration"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("ui_configuration_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    requests: Mapped[bool] = mapped_column("requests", Boolean, nullable=False)
    locations: Mapped[bool] = mapped_column("locations", Boolean, nullable=False)
    meters: Mapped[bool] = mapped_column("meters", Boolean, nullable=False)
    vendors_and_customers: Mapped[bool] = mapped_column("vendors_and_customers", Boolean, nullable=False)
    company_settings_id: Mapped[int] = mapped_column("company_settings_id", BigInteger, ForeignKey("company_settings.id", ondelete="CASCADE"), nullable=False)


class ShiftConfiguration(Base):
    __tablename__ = "shift_configuration"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("shift_configuration_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    enabled: Mapped[bool] = mapped_column("enabled", Boolean, nullable=False)


class CustomSequence(Base):
    __tablename__ = "custom_sequence"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("custom_sequence_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    work_order_sequence: Mapped[int] = mapped_column("work_order_sequence", BigInteger, nullable=False)
    asset_sequence: Mapped[int] = mapped_column("asset_sequence", BigInteger, nullable=False)
    preventive_maintenance_sequence: Mapped[int] = mapped_column("preventive_maintenance_sequence", BigInteger, nullable=False)
    location_sequence: Mapped[int] = mapped_column("location_sequence", BigInteger, nullable=False)
    request_sequence: Mapped[int] = mapped_column("request_sequence", BigInteger, nullable=False)
