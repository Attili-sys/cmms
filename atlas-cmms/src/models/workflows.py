"""SQLAlchemy models for group: workflows."""

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


class Workflow(Base):
    __tablename__ = "workflow"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("workflow_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    main_condition: Mapped[int] = mapped_column("main_condition", SmallInteger, nullable=False)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    action_id: Mapped[int] = mapped_column("action_id", BigInteger, ForeignKey("workflow_action.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column("title", String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column("enabled", Boolean, nullable=False)


class WorkflowCondition(Base):
    __tablename__ = "workflow_condition"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("workflow_condition_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    created_time_end: Mapped[int | None] = mapped_column("created_time_end", Integer, nullable=True)
    created_time_start: Mapped[int | None] = mapped_column("created_time_start", Integer, nullable=True)
    priority: Mapped[int | None] = mapped_column("priority", SmallInteger, nullable=True)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    asset_id: Mapped[int | None] = mapped_column("asset_id", BigInteger, ForeignKey("asset.id", ondelete="CASCADE"), nullable=True)
    location_id: Mapped[int | None] = mapped_column("location_id", BigInteger, ForeignKey("location.id", ondelete="CASCADE"), nullable=True)
    team_id: Mapped[int | None] = mapped_column("team_id", BigInteger, ForeignKey("team.id", ondelete="CASCADE"), nullable=True)
    user_id: Mapped[int | None] = mapped_column("user_id", BigInteger, ForeignKey("own_user.id", ondelete="CASCADE"), nullable=True)
    label: Mapped[str | None] = mapped_column("label", String(255), nullable=True)
    number_value: Mapped[int | None] = mapped_column("number_value", Integer, nullable=True)
    part_condition: Mapped[int | None] = mapped_column("part_condition", SmallInteger, nullable=True)
    purchase_order_condition: Mapped[int | None] = mapped_column("purchase_order_condition", SmallInteger, nullable=True)
    purchase_order_status: Mapped[int | None] = mapped_column("purchase_order_status", SmallInteger, nullable=True)
    request_condition: Mapped[int | None] = mapped_column("request_condition", SmallInteger, nullable=True)
    task_condition: Mapped[int | None] = mapped_column("task_condition", SmallInteger, nullable=True)
    value: Mapped[str | None] = mapped_column("value", String(255), nullable=True)
    work_order_condition: Mapped[int | None] = mapped_column("work_order_condition", SmallInteger, nullable=True)
    work_order_status: Mapped[int | None] = mapped_column("work_order_status", SmallInteger, nullable=True)
    part_id: Mapped[int | None] = mapped_column("part_id", BigInteger, ForeignKey("part.id", ondelete="CASCADE"), nullable=True)
    purchase_order_category_id: Mapped[int | None] = mapped_column("purchase_order_category_id", BigInteger, ForeignKey("purchase_order_category.id", ondelete="CASCADE"), nullable=True)
    vendor_id: Mapped[int | None] = mapped_column("vendor_id", BigInteger, ForeignKey("vendor.id", ondelete="CASCADE"), nullable=True)
    work_order_category_id: Mapped[int | None] = mapped_column("work_order_category_id", BigInteger, ForeignKey("work_order_category.id", ondelete="CASCADE"), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column("end_date", DateTime, nullable=True)
    start_date: Mapped[datetime | None] = mapped_column("start_date", DateTime, nullable=True)


class WorkflowAction(Base):
    __tablename__ = "workflow_action"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("workflow_action_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    priority: Mapped[int | None] = mapped_column("priority", SmallInteger, nullable=True)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    asset_id: Mapped[int | None] = mapped_column("asset_id", BigInteger, ForeignKey("asset.id", ondelete="CASCADE"), nullable=True)
    checklist_id: Mapped[int | None] = mapped_column("checklist_id", BigInteger, ForeignKey("checklist.id", ondelete="CASCADE"), nullable=True)
    location_id: Mapped[int | None] = mapped_column("location_id", BigInteger, ForeignKey("location.id", ondelete="CASCADE"), nullable=True)
    team_id: Mapped[int | None] = mapped_column("team_id", BigInteger, ForeignKey("team.id", ondelete="CASCADE"), nullable=True)
    user_id: Mapped[int | None] = mapped_column("user_id", BigInteger, ForeignKey("own_user.id", ondelete="SET NULL"), nullable=True)
    asset_status: Mapped[int | None] = mapped_column("asset_status", SmallInteger, nullable=True)
    part_action: Mapped[int | None] = mapped_column("part_action", SmallInteger, nullable=True)
    purchase_order_action: Mapped[int | None] = mapped_column("purchase_order_action", SmallInteger, nullable=True)
    request_action: Mapped[int | None] = mapped_column("request_action", SmallInteger, nullable=True)
    task_action: Mapped[int | None] = mapped_column("task_action", SmallInteger, nullable=True)
    work_order_action: Mapped[int | None] = mapped_column("work_order_action", SmallInteger, nullable=True)
    purchase_order_category_id: Mapped[int | None] = mapped_column("purchase_order_category_id", BigInteger, ForeignKey("purchase_order_category.id", ondelete="CASCADE"), nullable=True)
    vendor_id: Mapped[int | None] = mapped_column("vendor_id", BigInteger, ForeignKey("vendor.id", ondelete="CASCADE"), nullable=True)
    work_order_category_id: Mapped[int | None] = mapped_column("work_order_category_id", BigInteger, ForeignKey("work_order_category.id", ondelete="CASCADE"), nullable=True)
    number_value: Mapped[int | None] = mapped_column("number_value", Integer, nullable=True)
    value: Mapped[str | None] = mapped_column("value", String(255), nullable=True)
