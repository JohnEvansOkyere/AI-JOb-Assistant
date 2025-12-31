"""
Subscription Plan Configuration
Central configuration for all subscription plans, limits, and features.

To modify pricing or features, update this file and follow the guide in:
docs/HOW_TO_CHANGE_PRICING.md
"""

from typing import Dict, Any, Optional
from decimal import Decimal

# Current exchange rate: ~12 GHS per USD (update monthly)
USD_TO_GHS_EXCHANGE_RATE = 12.0


def convert_usd_to_ghs(usd_amount: float, exchange_rate: float = USD_TO_GHS_EXCHANGE_RATE) -> float:
    """Convert USD to GHS, rounded to nearest whole number"""
    return round(usd_amount * exchange_rate, 0)


# Plan definitions
SUBSCRIPTION_PLANS: Dict[str, Dict[str, Any]] = {
    "free": {
        "name": "Free",
        "price_monthly_usd": 0.00,
        "price_monthly_ghs": 0.00,
        "trial_days": 14,
        "limits": {
            "monthly_interview_limit": 5,  # Very limited for free
            "daily_cost_limit_usd": Decimal("1.00"),
            "monthly_cost_limit_usd": Decimal("10.00"),
            "max_active_jobs": 1,
        },
        "features": {
            "cv_screening": True,
            "basic_analytics": True,
            "email_support": True,
            "advanced_analytics": False,
            "priority_email_support": False,
            "api_access": False,
            "sso": False,
            "custom_workflows": False,
            "team_collaboration": False,
            "dedicated_support": False,
            "custom_analytics": False,
            "custom_onboarding": False,
        },
    },
    "starter": {
        "name": "Starter",
        "price_monthly_usd": 49.00,
        "price_monthly_ghs": convert_usd_to_ghs(49.00),
        "trial_days": 14,
        "limits": {
            "monthly_interview_limit": 50,
            "daily_cost_limit_usd": Decimal("10.00"),
            "monthly_cost_limit_usd": Decimal("100.00"),
            "max_active_jobs": 1,
        },
        "features": {
            "cv_screening": True,
            "basic_analytics": True,
            "email_support": True,
            "advanced_analytics": False,
            "priority_email_support": False,
            "api_access": False,
            "sso": False,
            "custom_workflows": False,
            "team_collaboration": False,
            "dedicated_support": False,
            "custom_analytics": False,
            "custom_onboarding": False,
        },
    },
    "professional": {
        "name": "Professional",
        "price_monthly_usd": 149.00,
        "price_monthly_ghs": convert_usd_to_ghs(149.00),
        "trial_days": 14,
        "limits": {
            "monthly_interview_limit": 200,
            "daily_cost_limit_usd": Decimal("50.00"),
            "monthly_cost_limit_usd": Decimal("500.00"),
            "max_active_jobs": 5,
        },
        "features": {
            "cv_screening": True,
            "basic_analytics": True,
            "advanced_analytics": True,
            "priority_email_support": True,
            "custom_workflows": True,
            "team_collaboration": True,
            "email_support": True,
            "api_access": False,
            "sso": False,
            "dedicated_support": False,
            "custom_analytics": False,
            "custom_onboarding": False,
        },
    },
    "enterprise": {
        "name": "Enterprise",
        "price_monthly_usd": None,  # Custom pricing
        "price_monthly_ghs": None,
        "trial_days": 14,
        "limits": {
            "monthly_interview_limit": None,  # Unlimited
            "daily_cost_limit_usd": None,  # Unlimited (or custom)
            "monthly_cost_limit_usd": None,  # Unlimited (or custom)
            "max_active_jobs": None,  # Unlimited
        },
        "features": {
            "cv_screening": True,
            "basic_analytics": True,
            "advanced_analytics": True,
            "custom_analytics": True,
            "priority_email_support": True,
            "dedicated_support": True,
            "api_access": True,
            "sso": True,
            "custom_workflows": True,
            "team_collaboration": True,
            "custom_onboarding": True,
            "email_support": True,
        },
    },
    "custom": {
        "name": "Custom",
        "price_monthly_usd": None,
        "price_monthly_ghs": None,
        "trial_days": 14,
        "limits": {
            "monthly_interview_limit": None,  # Set manually
            "daily_cost_limit_usd": None,
            "monthly_cost_limit_usd": None,
            "max_active_jobs": None,
        },
        "features": {
            "cv_screening": True,
            "basic_analytics": True,
            "advanced_analytics": True,
            "custom_analytics": True,
            "priority_email_support": True,
            "dedicated_support": True,
            "api_access": True,
            "sso": True,
            "custom_workflows": True,
            "team_collaboration": True,
            "custom_onboarding": True,
            "email_support": True,
        },
    },
}


class SubscriptionPlanService:
    """Service for managing subscription plan configurations"""

    @staticmethod
    def get_plan_config(plan_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a subscription plan
        
        Args:
            plan_name: Plan identifier ('free', 'starter', 'professional', 'enterprise', 'custom')
        
        Returns:
            Plan configuration dict or None if plan not found
        """
        return SUBSCRIPTION_PLANS.get(plan_name.lower())

    @staticmethod
    def get_all_plans() -> Dict[str, Dict[str, Any]]:
        """
        Get all available subscription plans
        
        Returns:
            Dictionary of all plan configurations
        """
        return SUBSCRIPTION_PLANS.copy()

    @staticmethod
    def get_plan_limits(plan_name: str) -> Optional[Dict[str, Any]]:
        """
        Get limits for a specific plan
        
        Args:
            plan_name: Plan identifier
        
        Returns:
            Limits dict or None if plan not found
        """
        plan = SubscriptionPlanService.get_plan_config(plan_name)
        if plan:
            return plan.get("limits", {})
        return None

    @staticmethod
    def get_plan_features(plan_name: str) -> Optional[Dict[str, bool]]:
        """
        Get features for a specific plan
        
        Args:
            plan_name: Plan identifier
        
        Returns:
            Features dict or None if plan not found
        """
        plan = SubscriptionPlanService.get_plan_config(plan_name)
        if plan:
            return plan.get("features", {})
        return None

    @staticmethod
    def has_feature(plan_name: str, feature_name: str) -> bool:
        """
        Check if a plan has a specific feature
        
        Args:
            plan_name: Plan identifier
            feature_name: Feature to check
        
        Returns:
            True if plan has feature, False otherwise
        """
        features = SubscriptionPlanService.get_plan_features(plan_name)
        if features:
            return features.get(feature_name, False)
        return False

    @staticmethod
    def get_plan_price(plan_name: str, currency: str = "usd") -> Optional[float]:
        """
        Get price for a plan in specified currency
        
        Args:
            plan_name: Plan identifier
            currency: 'usd' or 'ghs'
        
        Returns:
            Price or None if not available
        """
        plan = SubscriptionPlanService.get_plan_config(plan_name)
        if not plan:
            return None
        
        if currency.lower() == "ghs":
            return plan.get("price_monthly_ghs")
        else:
            return plan.get("price_monthly_usd")

