"""SQLAlchemy models for group: work_orders."""

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


class WorkOrder(Base):
    __tablename__ = "work_order"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("work_order_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
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
    archived: Mapped[bool] = mapped_column("archived", Boolean, nullable=False)
    completed_on: Mapped[datetime | None] = mapped_column("completed_on", DateTime, nullable=True)
    feedback: Mapped[str | None] = mapped_column("feedback", Text, nullable=True)
    status: Mapped[int | None] = mapped_column("status", SmallInteger, nullable=True)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    asset_id: Mapped[int | None] = mapped_column("asset_id", BigInteger, ForeignKey("asset.id", ondelete="SET NULL"), nullable=True)
    category_id: Mapped[int | None] = mapped_column("category_id", BigInteger, ForeignKey("work_order_category.id", ondelete="SET NULL"), nullable=True)
    image_id: Mapped[int | None] = mapped_column("image_id", BigInteger, ForeignKey("file.id", ondelete="SET NULL"), nullable=True)
    location_id: Mapped[int | None] = mapped_column("location_id", BigInteger, ForeignKey("location.id", ondelete="SET NULL"), nullable=True)
    primary_user_id: Mapped[int | None] = mapped_column("primary_user_id", BigInteger, ForeignKey("own_user.id", ondelete="SET NULL"), nullable=True)
    team_id: Mapped[int | None] = mapped_column("team_id", BigInteger, ForeignKey("team.id", ondelete="SET NULL"), nullable=True)
    completed_by_id: Mapped[int | None] = mapped_column("completed_by_id", BigInteger, ForeignKey("own_user.id", ondelete="SET NULL"), nullable=True)
    parent_preventive_maintenance_id: Mapped[int | None] = mapped_column("parent_preventive_maintenance_id", BigInteger, ForeignKey("preventive_maintenance.id", ondelete="SET NULL"), nullable=True)
    parent_request_id: Mapped[int | None] = mapped_column("parent_request_id", BigInteger, ForeignKey("request.id", ondelete="SET NULL"), nullable=True)
    signature_id: Mapped[int | None] = mapped_column("signature_id", BigInteger, ForeignKey("file.id", ondelete="SET NULL"), nullable=True)
    first_time_to_react: Mapped[datetime | None] = mapped_column("first_time_to_react", DateTime, nullable=True)
    estimated_start_date: Mapped[datetime | None] = mapped_column("estimated_start_date", DateTime, nullable=True)
    custom_id: Mapped[str | None] = mapped_column("custom_id", String(255), nullable=True)
    signature: Mapped[str | None] = mapped_column("signature", Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column("is_demo", Boolean, nullable=False)


class WorkOrderHistory(Base):
    __tablename__ = "work_order_history"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("work_order_history_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    user_id: Mapped[int] = mapped_column("user_id", BigInteger, ForeignKey("own_user.id", ondelete="CASCADE"), nullable=False)
    work_order_id: Mapped[int] = mapped_column("work_order_id", BigInteger, ForeignKey("work_order.id", ondelete="CASCADE"), nullable=False)


class Labor(Base):
    __tablename__ = "labor"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("labor_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    duration: Mapped[int] = mapped_column("duration", BigInteger, nullable=False)
    hourly_rate: Mapped[int] = mapped_column("hourly_rate", BigInteger, nullable=False)
    include_to_total_time: Mapped[bool] = mapped_column("include_to_total_time", Boolean, nullable=False)
    logged: Mapped[bool] = mapped_column("logged", Boolean, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column("started_at", DateTime, nullable=True)
    status: Mapped[int | None] = mapped_column("status", SmallInteger, nullable=True)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    assigned_to_id: Mapped[int | None] = mapped_column("assigned_to_id", BigInteger, ForeignKey("own_user.id", ondelete="SET NULL"), nullable=True)
    time_category_id: Mapped[int | None] = mapped_column("time_category_id", BigInteger, ForeignKey("time_category.id", ondelete="SET NULL"), nullable=True)
    work_order_id: Mapped[int] = mapped_column("work_order_id", BigInteger, ForeignKey("work_order.id", ondelete="CASCADE"), nullable=False)
    is_demo: Mapped[bool] = mapped_column("is_demo", Boolean, nullable=False)


class Relation(Base):
    __tablename__ = "relation"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("relation_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    relation_type: Mapped[int] = mapped_column("relation_type", SmallInteger, nullable=False)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    child_id: Mapped[int] = mapped_column("child_id", BigInteger, ForeignKey("work_order.id", ondelete="CASCADE"), nullable=False)
    parent_id: Mapped[int] = mapped_column("parent_id", BigInteger, ForeignKey("work_order.id", ondelete="CASCADE"), nullable=False)


class Comment(Base):
    __tablename__ = "comment"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("comment_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    work_order_id: Mapped[int] = mapped_column("work_order_id", BigInteger, ForeignKey("work_order.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column("user_id", BigInteger, ForeignKey("own_user.id", ondelete="CASCADE"), nullable=False)
    content: Mapped[str] = mapped_column("content", Text, nullable=False)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
