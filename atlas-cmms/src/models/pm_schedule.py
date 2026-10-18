"""SQLAlchemy models for group: pm_schedule."""

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
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column

from src.models._base import Base, utcnow


class PreventiveMaintenance(Base):
    __tablename__ = "preventive_maintenance"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("preventive_maintenance_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
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
    name: Mapped[str | None] = mapped_column("name", String(255), nullable=True)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    asset_id: Mapped[int | None] = mapped_column("asset_id", BigInteger, ForeignKey("asset.id", ondelete="SET NULL"), nullable=True)
    category_id: Mapped[int | None] = mapped_column("category_id", BigInteger, ForeignKey("work_order_category.id", ondelete="SET NULL"), nullable=True)
    image_id: Mapped[int | None] = mapped_column("image_id", BigInteger, ForeignKey("file.id", ondelete="SET NULL"), nullable=True)
    location_id: Mapped[int | None] = mapped_column("location_id", BigInteger, ForeignKey("location.id", ondelete="SET NULL"), nullable=True)
    primary_user_id: Mapped[int | None] = mapped_column("primary_user_id", BigInteger, ForeignKey("own_user.id", ondelete="SET NULL"), nullable=True)
    team_id: Mapped[int | None] = mapped_column("team_id", BigInteger, ForeignKey("team.id", ondelete="SET NULL"), nullable=True)
    schedule_id: Mapped[int | None] = mapped_column("schedule_id", BigInteger, ForeignKey("schedule.id", ondelete="SET NULL"), nullable=True)
    estimated_start_date: Mapped[datetime | None] = mapped_column("estimated_start_date", DateTime, nullable=True)
    custom_id: Mapped[str | None] = mapped_column("custom_id", String(255), nullable=True)
    is_demo: Mapped[bool] = mapped_column("is_demo", Boolean, nullable=False)


class Schedule(Base):
    __tablename__ = "schedule"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("schedule_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    disabled: Mapped[bool] = mapped_column("disabled", Boolean, nullable=False)
    ends_on: Mapped[datetime | None] = mapped_column("ends_on", DateTime, nullable=True)
    frequency: Mapped[int] = mapped_column("frequency", Integer, nullable=False)
    starts_on: Mapped[datetime] = mapped_column("starts_on", DateTime, nullable=False)
    preventive_maintenance_id: Mapped[int | None] = mapped_column("preventive_maintenance_id", BigInteger, ForeignKey("preventive_maintenance.id", ondelete="CASCADE"), nullable=True)
    due_date_delay: Mapped[int | None] = mapped_column("due_date_delay", Integer, nullable=True)
    recurrence_type: Mapped[str] = mapped_column("recurrence_type", String(255), nullable=False)
    recurrence_based_on: Mapped[str] = mapped_column("recurrence_based_on", String(255), nullable=False)
    is_demo: Mapped[bool] = mapped_column("is_demo", Boolean, nullable=False)

    @hybrid_property
    def next_due_date(self) -> datetime:
        return self.starts_on

    @next_due_date.setter
    def next_due_date(self, value: datetime) -> None:
        self.starts_on = value

    @next_due_date.expression
    def next_due_date(cls):
        return cls.starts_on
