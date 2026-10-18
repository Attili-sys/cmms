"""DeclarativeBase and shared JPA @MappedSuperclass mixins for Atlas CMMS models."""

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    Sequence,
    SmallInteger,
    String,
    Text,
    event,
    func,
)
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


@compiles(BigInteger, "sqlite")
def _compile_biginteger_sqlite(element, compiler, **kw) -> str:
    return "INTEGER"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Single SQLAlchemy DeclarativeBase for all 73 entity tables and 54 association tables."""


@event.listens_for(Base, "before_insert", propagate=True)
def _apply_java_primitive_defaults(mapper, connection, target) -> None:
    """Replicate Java primitive field defaults (boolean=False, int=0, float=0.0) for unset NOT NULL columns."""
    for col in mapper.columns:
        if col.primary_key or col.nullable or col.foreign_keys:
            continue
        if getattr(target, col.key, None) is not None:
            continue
        col_type = col.type
        if isinstance(col_type, Boolean):
            setattr(target, col.key, False)
        elif isinstance(col_type, (Integer, SmallInteger, BigInteger)):
            setattr(target, col.key, 0)
        elif isinstance(col_type, (Float, Numeric)):
            setattr(target, col.key, 0.0)
        elif isinstance(col_type, DateTime):
            setattr(target, col.key, utcnow())
        elif isinstance(col_type, (String, Text)):
            fallback = (
                getattr(target, "title", None)
                or getattr(target, "name", None)
                or getattr(target, "label", None)
                or ""
            )
            setattr(target, col.key, fallback)


def pk_seq(seq_name: str, increment: int = 50):
    """Primary key column backed by a PostgreSQL sequence (matching Hibernate allocationSize)."""
    seq = Sequence(seq_name, start=1, increment=increment, metadata=Base.metadata)
    return mapped_column(BigInteger, seq, primary_key=True, autoincrement=True, nullable=False)




class DateAuditMixin:
    """Matches com.grash.model.abstracts.DateAudit."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, server_default=func.now(), nullable=False
    )


class AuditMixin(DateAuditMixin):
    """Matches com.grash.model.abstracts.Audit."""

    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("own_user.id", ondelete="SET NULL"), nullable=True
    )
    updated_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("own_user.id", ondelete="SET NULL"), nullable=True
    )


class CompanyAuditMixin(AuditMixin):
    """Matches com.grash.model.abstracts.CompanyAudit."""

    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False
    )
