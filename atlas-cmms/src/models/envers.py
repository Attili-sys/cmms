"""SQLAlchemy models for group: envers."""

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

from src.models._base import Base


class RevInfo(Base):
    __tablename__ = "revinfo"

    rev: Mapped[int] = mapped_column("rev", Integer, Sequence("hibernate_sequence", start=1, increment=1, metadata=Base.metadata), primary_key=True, nullable=False)
    revtstmp: Mapped[int] = mapped_column("revtstmp", BigInteger, nullable=False)
    user_id: Mapped[int | None] = mapped_column("user_id", BigInteger, nullable=True)


class WorkOrderAud(Base):
    __tablename__ = "work_order_aud"

    rev: Mapped[int] = mapped_column("rev", Integer, primary_key=True, nullable=False)
    revtype: Mapped[int | None] = mapped_column("revtype", Integer, nullable=True)
    priority: Mapped[int | None] = mapped_column("priority", SmallInteger, nullable=True)
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    title: Mapped[str | None] = mapped_column("title", String(255), nullable=True)
    image_id: Mapped[int | None] = mapped_column("image_id", BigInteger, ForeignKey("file.id", ondelete="SET NULL"), nullable=True)
    category_id: Mapped[int | None] = mapped_column("category_id", BigInteger, ForeignKey("work_order_category.id", ondelete="SET NULL"), nullable=True)
    location_id: Mapped[int | None] = mapped_column("location_id", BigInteger, ForeignKey("location.id", ondelete="SET NULL"), nullable=True)
    team_id: Mapped[int | None] = mapped_column("team_id", BigInteger, ForeignKey("team.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[int | None] = mapped_column("status", SmallInteger, nullable=True)
    signature_id: Mapped[int | None] = mapped_column("signature_id", BigInteger, ForeignKey("file.id", ondelete="SET NULL"), nullable=True)
    archived: Mapped[bool | None] = mapped_column("archived", Boolean, nullable=True)
    feedback: Mapped[str | None] = mapped_column("feedback", Text, nullable=True)
    priority_mod: Mapped[bool | None] = mapped_column("priority_mod", Boolean, nullable=True)
    description_mod: Mapped[bool | None] = mapped_column("description_mod", Boolean, nullable=True)
    title_mod: Mapped[bool | None] = mapped_column("title_mod", Boolean, nullable=True)
    status_mod: Mapped[bool | None] = mapped_column("status_mod", Boolean, nullable=True)
    archived_mod: Mapped[bool | None] = mapped_column("archived_mod", Boolean, nullable=True)
    feedback_mod: Mapped[bool | None] = mapped_column("feedback_mod", Boolean, nullable=True)
    completed_on: Mapped[datetime | None] = mapped_column("completed_on", DateTime, nullable=True)
    primary_user_id: Mapped[int | None] = mapped_column("primary_user_id", BigInteger, ForeignKey("own_user.id", ondelete="SET NULL"), nullable=True)
    completed_by_id: Mapped[int | None] = mapped_column("completed_by_id", BigInteger, ForeignKey("own_user.id", ondelete="SET NULL"), nullable=True)
    parent_request_id: Mapped[int | None] = mapped_column("parent_request_id", BigInteger, ForeignKey("request.id", ondelete="SET NULL"), nullable=True)
    parent_preventive_maintenance_id: Mapped[int | None] = mapped_column("parent_preventive_maintenance_id", BigInteger, ForeignKey("preventive_maintenance.id", ondelete="SET NULL"), nullable=True)
    asset_id: Mapped[int | None] = mapped_column("asset_id", BigInteger, nullable=True)
    id: Mapped[int] = mapped_column("id", BigInteger, ForeignKey("work_order.id"), nullable=False)
    due_date: Mapped[datetime | None] = mapped_column("due_date", DateTime, nullable=True)
    estimated_duration: Mapped[float | None] = mapped_column("estimated_duration", Float, nullable=True)
    required_signature: Mapped[bool | None] = mapped_column("required_signature", Boolean, nullable=True)
    location_mod: Mapped[bool | None] = mapped_column("location_mod", Boolean, nullable=True)
    team_mod: Mapped[bool | None] = mapped_column("team_mod", Boolean, nullable=True)
    category_mod: Mapped[bool | None] = mapped_column("category_mod", Boolean, nullable=True)
    signature_mod: Mapped[bool | None] = mapped_column("signature_mod", Boolean, nullable=True)
    asset_mod: Mapped[bool | None] = mapped_column("asset_mod", Boolean, nullable=True)
    image_mod: Mapped[bool | None] = mapped_column("image_mod", Boolean, nullable=True)
    due_date_mod: Mapped[bool | None] = mapped_column("due_date_mod", Boolean, nullable=True)
    required_signature_mod: Mapped[bool | None] = mapped_column("required_signature_mod", Boolean, nullable=True)
    estimated_duration_mod: Mapped[bool | None] = mapped_column("estimated_duration_mod", Boolean, nullable=True)
    primary_user_mod: Mapped[bool | None] = mapped_column("primary_user_mod", Boolean, nullable=True)
    completed_by_mod: Mapped[bool | None] = mapped_column("completed_by_mod", Boolean, nullable=True)
    completed_on_mod: Mapped[bool | None] = mapped_column("completed_on_mod", Boolean, nullable=True)
    parent_request_mod: Mapped[bool | None] = mapped_column("parent_request_mod", Boolean, nullable=True)
    parent_preventive_maintenance_mod: Mapped[bool | None] = mapped_column("parent_preventive_maintenance_mod", Boolean, nullable=True)
    estimated_start_date: Mapped[datetime | None] = mapped_column("estimated_start_date", DateTime, nullable=True)
    estimated_start_date_mod: Mapped[bool | None] = mapped_column("estimated_start_date_mod", Boolean, nullable=True)
    custom_id: Mapped[str | None] = mapped_column("custom_id", String(255), nullable=True)
    custom_id_mod: Mapped[bool | None] = mapped_column("custom_id_mod", Boolean, nullable=True)
    signature: Mapped[str | None] = mapped_column("signature", Text, nullable=True)
    is_demo: Mapped[bool | None] = mapped_column("is_demo", Boolean, nullable=True)
    is_demo_mod: Mapped[bool | None] = mapped_column("is_demo_mod", Boolean, nullable=True)

company_custom_field_seq = Sequence("company_custom_field_seq", start=1, increment=50, metadata=Base.metadata)
