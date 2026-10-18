"""SQLAlchemy models for group: users."""

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
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.models._base import Base, utcnow


class User(Base):
    __tablename__ = "own_user"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("own_user_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    email: Mapped[str] = mapped_column("email", String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column("enabled", Boolean, nullable=False)
    first_name: Mapped[str] = mapped_column("first_name", String(255), nullable=False)
    job_title: Mapped[str | None] = mapped_column("job_title", String(255), nullable=True)
    last_name: Mapped[str] = mapped_column("last_name", String(255), nullable=False)
    owns_company: Mapped[bool] = mapped_column("owns_company", Boolean, nullable=False)
    password: Mapped[str] = mapped_column("password", String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column("phone", String(255), nullable=True)
    rate: Mapped[int] = mapped_column("rate", BigInteger, nullable=False)
    username: Mapped[str] = mapped_column("username", String(255), nullable=False)
    company_id: Mapped[int | None] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=True)
    image_id: Mapped[int | None] = mapped_column("image_id", BigInteger, ForeignKey("file.id", ondelete="SET NULL"), nullable=True)
    location_id: Mapped[int | None] = mapped_column("location_id", BigInteger, ForeignKey("location.id", ondelete="SET NULL"), nullable=True)
    role_id: Mapped[int] = mapped_column("role_id", BigInteger, ForeignKey("role.id", ondelete="CASCADE"), nullable=False)
    user_settings_id: Mapped[int | None] = mapped_column("user_settings_id", BigInteger, ForeignKey("user_settings.id", ondelete="SET NULL"), nullable=True)
    enabled_in_subscription: Mapped[bool] = mapped_column("enabled_in_subscription", Boolean, nullable=False)
    last_login: Mapped[datetime | None] = mapped_column("last_login", DateTime, nullable=True)
    created_via_sso: Mapped[bool] = mapped_column("created_via_sso", Boolean, nullable=False)
    sso_provider: Mapped[str | None] = mapped_column("sso_provider", String(255), nullable=True)
    sso_provider_id: Mapped[str | None] = mapped_column("sso_provider_id", String(255), nullable=True)
    gclid: Mapped[str | None] = mapped_column("gclid", String(255), nullable=True)
    utm_source: Mapped[str | None] = mapped_column("utm_source", String(255), nullable=True)
    utm_medium: Mapped[str | None] = mapped_column("utm_medium", String(255), nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column("utm_campaign", String(255), nullable=True)
    utm_term: Mapped[str | None] = mapped_column("utm_term", String(255), nullable=True)
    utm_content: Mapped[str | None] = mapped_column("utm_content", String(255), nullable=True)
    fbclid: Mapped[str | None] = mapped_column("fbclid", String(255), nullable=True)
    referrer: Mapped[str | None] = mapped_column("referrer", Text, nullable=True)
    paddle_user_id: Mapped[str | None] = mapped_column("paddle_user_id", String(255), nullable=True)
    app_stats_id: Mapped[int | None] = mapped_column("app_stats_id", BigInteger, ForeignKey("user_app_stats.id", ondelete="SET NULL"), nullable=True)
    shift_configuration_id: Mapped[int | None] = mapped_column("shift_configuration_id", BigInteger, ForeignKey("shift_configuration.id", ondelete="SET NULL"), nullable=True)
    session_invalidated_at: Mapped[datetime | None] = mapped_column("session_invalidated_at", DateTime, nullable=True)
    language: Mapped[int | None] = mapped_column("language", Integer, nullable=True)


class Role(Base):
    __tablename__ = "role"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("role_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    code: Mapped[int | None] = mapped_column("code", SmallInteger, nullable=True)
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    external_id: Mapped[str | None] = mapped_column("external_id", String(255), nullable=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    paid: Mapped[bool] = mapped_column("paid", Boolean, nullable=False)
    role_type: Mapped[int] = mapped_column("role_type", SmallInteger, nullable=False)
    company_settings_id: Mapped[int | None] = mapped_column("company_settings_id", BigInteger, ForeignKey("company_settings.id", ondelete="CASCADE"), nullable=True)


class Team(Base):
    __tablename__ = "team"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("team_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("user_settings_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    email_notified: Mapped[bool] = mapped_column("email_notified", Boolean, nullable=False)
    email_updates_for_purchase_orders: Mapped[bool] = mapped_column("email_updates_for_purchase_orders", Boolean, nullable=False)
    email_updates_for_requests: Mapped[bool] = mapped_column("email_updates_for_requests", Boolean, nullable=False)
    email_updates_for_work_orders: Mapped[bool] = mapped_column("email_updates_for_work_orders", Boolean, nullable=False)
    stats_for_assigned_work_orders: Mapped[bool] = mapped_column("stats_for_assigned_work_orders", Boolean, nullable=False)


class UserInvitation(Base):
    __tablename__ = "user_invitation"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("user_invitation_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    email: Mapped[str] = mapped_column("email", String(255), nullable=False)
    role_id: Mapped[int] = mapped_column("role_id", BigInteger, ForeignKey("role.id", ondelete="CASCADE"), nullable=False)


class SuperAccountRelation(Base):
    __tablename__ = "super_account_relation"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("super_account_relation_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    super_user_id: Mapped[int] = mapped_column("super_user_id", BigInteger, ForeignKey("own_user.id", ondelete="CASCADE"), nullable=False)
    child_user_id: Mapped[int] = mapped_column("child_user_id", BigInteger, ForeignKey("own_user.id", ondelete="CASCADE"), nullable=False)


class UserAppStats(Base):
    __tablename__ = "user_app_stats"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("user_app_stats_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, nullable=False, default=utcnow)
    created_by: Mapped[int | None] = mapped_column("created_by", BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column("updated_by", BigInteger, nullable=True)
    completed_work_orders: Mapped[int] = mapped_column("completed_work_orders", Integer, nullable=False)
    app_sessions: Mapped[int] = mapped_column("app_sessions", Integer, nullable=False)
    last_review_prompt_at: Mapped[datetime | None] = mapped_column("last_review_prompt_at", DateTime, nullable=True)
    review_prompt_shown_count: Mapped[int] = mapped_column("review_prompt_shown_count", Integer, nullable=False)
    review_click_count: Mapped[int] = mapped_column("review_click_count", Integer, nullable=False)
    has_rated_app: Mapped[bool] = mapped_column("has_rated_app", Boolean, nullable=False)
    feedback: Mapped[str | None] = mapped_column("feedback", Text, nullable=True)


class VerificationToken(Base):
    __tablename__ = "verification_token"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("verification_token_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column("created_at", DateTime, nullable=True, default=utcnow)
    expiry_date: Mapped[datetime | None] = mapped_column("expiry_date", DateTime, nullable=True)
    token: Mapped[str | None] = mapped_column("token", String(255), nullable=True)
    user_id: Mapped[int] = mapped_column("user_id", BigInteger, ForeignKey("own_user.id", ondelete="CASCADE"), nullable=False)
    payload: Mapped[str | None] = mapped_column("payload", String(255), nullable=True)


class RefreshToken(Base):
    __tablename__ = "refresh_token"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, nullable=False)
    token_hash: Mapped[str] = mapped_column("token_hash", String(255), nullable=False)
    user_id: Mapped[int] = mapped_column("user_id", BigInteger, ForeignKey("own_user.id", ondelete="CASCADE"), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column("expires_at", DateTime, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column("created_at", DateTime, nullable=True, default=utcnow)
    revoked: Mapped[bool | None] = mapped_column("revoked", Boolean, nullable=True)
    replaced_by_token_hash: Mapped[str | None] = mapped_column("replaced_by_token_hash", String(255), nullable=True)


class PushNotificationToken(Base):
    __tablename__ = "push_notification_token"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("push_notification_token_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    token: Mapped[str | None] = mapped_column("token", String(255), nullable=True)
    user_id: Mapped[int] = mapped_column("user_id", BigInteger, ForeignKey("own_user.id", ondelete="CASCADE"), nullable=False)
