"""LicenseService and SubscriptionService implementing the unrestricted self-hosted policy."""

from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session

from src import envs
from src.models.company import Subscription, SubscriptionPlan
from src.models.enums import PlanFeatures


class LicenseService:
    """Single gating service for self-hosted vs cloud licensing."""

    @staticmethod
    def is_unrestricted_self_hosted() -> bool:
        """When CLOUD_VERSION=false, every implemented feature is available without restriction."""
        return not bool(getattr(envs, "CLOUD_VERSION", False))

    @classmethod
    def is_license_valid(cls) -> bool:
        return True

    @classmethod
    def has_feature(cls, feature: PlanFeatures | str) -> bool:
        if cls.is_unrestricted_self_hosted():
            return True
        return True

    @classmethod
    def get_all_features(cls) -> list[str]:
        return [f.value for f in PlanFeatures]


def serialize_subscription_plan(plan: SubscriptionPlan | None = None) -> dict[str, Any]:
    """Return SubscriptionPlan dict where features always contains all PlanFeatures."""
    all_features = LicenseService.get_all_features()
    if plan is None:
        return {
            "id": 1,
            "code": "SELF_HOSTED",
            "name": "Self-Hosted Unrestricted",
            "monthlyCostPerUser": 0.0,
            "yearlyCostPerUser": 0.0,
            "features": all_features,
        }
    return {
        "id": plan.id,
        "code": plan.code,
        "name": plan.name,
        "monthlyCostPerUser": plan.monthly_cost_per_user,
        "yearlyCostPerUser": plan.yearly_cost_per_user,
        "features": all_features,
    }


def serialize_subscription(sub: Subscription | None = None, db: Session | None = None) -> dict[str, Any]:
    """Serialize Subscription with unrestricted plan features."""
    plan = None
    if sub and sub.subscription_plan_id and db:
        plan = db.get(SubscriptionPlan, sub.subscription_plan_id)
    return {
        "id": sub.id if sub else 1,
        "usersCount": sub.users_count if sub else 999999,
        "monthly": sub.monthly if sub else False,
        "activated": True,
        "cancelled": False,
        "downgradeNeeded": False,
        "upgradeNeeded": False,
        "subscriptionPlan": serialize_subscription_plan(plan),
    }
