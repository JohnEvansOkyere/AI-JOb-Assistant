"""
Subscription API Routes
Handles subscription management, payment links, and Paystack webhooks
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body, Request, Header
from typing import Optional
from uuid import UUID
from app.schemas.common import Response
from app.services.payment_service import PaymentService
from app.services.usage_limit_checker import UsageLimitChecker
from app.config_plans import SubscriptionPlanService
from app.utils.auth import get_current_user_id, get_current_user
from app.database import db
from datetime import datetime, timedelta, timezone
import structlog
import json

logger = structlog.get_logger()

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("/create-payment-link", response_model=Response[dict])
async def create_payment_link(
    subscription_plan: str = Body(..., description="Subscription plan: starter, professional, enterprise"),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Create a Paystack payment link for subscription
    
    Args:
        subscription_plan: Plan to subscribe to
        recruiter_id: Current user ID
    
    Returns:
        Payment link URL from Paystack
    """
    try:
        # Validate plan
        plan_config = SubscriptionPlanService.get_plan_config(subscription_plan)
        if not plan_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subscription plan: {subscription_plan}"
            )
        
        # Get user and organization info
        user_response = (
            db.service_client.table("users")
            .select("email, company_name, full_name")
            .eq("id", str(recruiter_id))
            .execute()
        )
        
        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = user_response.data[0]
        company_name = user.get("company_name")
        email = user.get("email")
        
        if not company_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company name not set. Please set your company name first."
            )
        
        # Get plan price in GHS
        amount_ghs = SubscriptionPlanService.get_plan_price(subscription_plan, currency="ghs")
        if amount_ghs is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This plan requires custom pricing. Please contact sales."
            )
        
        # Create payment link
        payment_result = await PaymentService.create_payment_link(
            company_name=company_name,
            subscription_plan=subscription_plan,
            email=email,
            amount_ghs=amount_ghs,
            metadata={
                "user_id": str(recruiter_id),
                "user_name": user.get("full_name"),
            }
        )
        
        if not payment_result.get("status"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=payment_result.get("message", "Failed to create payment link")
            )
        
        data = payment_result.get("data", {})
        
        return Response(
            success=True,
            message="Payment link created successfully",
            data={
                "authorization_url": data.get("authorization_url"),
                "access_code": data.get("access_code"),
                "reference": data.get("reference"),
                "amount_ghs": amount_ghs,
                "subscription_plan": subscription_plan,
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating payment link", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/verify-payment", response_model=Response[dict])
async def verify_payment(
    reference: str = Body(..., description="Paystack transaction reference"),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Verify a Paystack payment transaction
    
    Args:
        reference: Transaction reference from Paystack
        recruiter_id: Current user ID
    
    Returns:
        Payment verification result
    """
    try:
        # Verify transaction with Paystack
        verification_result = await PaymentService.verify_transaction(reference)
        
        if not verification_result.get("status"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=verification_result.get("message", "Payment verification failed")
            )
        
        data = verification_result.get("data", {})
        metadata = data.get("metadata", {})
        company_name = metadata.get("company_name")
        subscription_plan = metadata.get("subscription_plan")
        
        # Verify user owns this transaction
        user_response = (
            db.service_client.table("users")
            .select("company_name")
            .eq("id", str(recruiter_id))
            .execute()
        )
        
        if not user_response.data or user_response.data[0].get("company_name") != company_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized: This payment does not belong to your account"
            )
        
        # Idempotency check: Verify payment wasn't already processed
        existing = (
            db.service_client.table("organization_settings")
            .select("last_payment_date, status")
            .eq("company_name", company_name)
            .execute()
        )
        
        payment_already_processed = False
        if existing.data:
            last_payment = existing.data[0].get("last_payment_date")
            if last_payment:
                last_payment_dt = datetime.fromisoformat(last_payment.replace('Z', '+00:00'))
                time_diff = datetime.utcnow().replace(tzinfo=timezone.utc) - last_payment_dt
                if time_diff.total_seconds() < 300:  # 5 minutes
                    payment_already_processed = True
                    logger.info(
                        "Payment already processed via webhook (idempotency)",
                        company_name=company_name,
                        reference=reference
                    )
        
        # Update organization settings with plan and limits (if not already processed)
        if subscription_plan and company_name and not payment_already_processed:
            # Set trial end date (14 days from now) - only if starting new subscription
            # If payment successful, activate subscription immediately
            trial_days = SubscriptionPlanService.get_plan_config(subscription_plan).get("trial_days", 14)
            
            # Assign plan limits
            await UsageLimitChecker.assign_plan_limits(company_name, subscription_plan)
            
            # Activate subscription (payment successful)
            update_data = {
                "status": "active",
                "subscription_starts_at": datetime.utcnow().isoformat(),
                "last_payment_date": datetime.utcnow().isoformat(),
                "subscription_ends_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "next_payment_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Only set trial_ends_at if subscription hasn't started yet
            existing_status = existing.data[0].get("status") if existing.data else None
            if existing_status == "trial":
                update_data["trial_ends_at"] = (datetime.utcnow() + timedelta(days=trial_days)).isoformat()
            
            db.service_client.table("organization_settings").update(update_data).eq(
                "company_name", company_name
            ).execute()
            
            logger.info(
                "Payment verified and subscription activated",
                company_name=company_name,
                subscription_plan=subscription_plan,
                reference=reference,
                source="direct_api"
            )
        
        return Response(
            success=True,
            message="Payment verified successfully",
            data={
                "reference": reference,
                "status": data.get("status"),
                "amount": data.get("amount") / 100,  # Convert from kobo/pesewas
                "subscription_plan": subscription_plan,
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error verifying payment", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def paystack_webhook(
    request: Request,
    x_paystack_signature: Optional[str] = Header(None)
):
    """
    Paystack webhook endpoint for payment events
    
    This endpoint receives webhooks from Paystack for:
    - charge.success: Payment successful
    - charge.failed: Payment failed
    - subscription.create: Subscription created
    - subscription.disable: Subscription cancelled
    
    Args:
        request: FastAPI request object
        x_paystack_signature: Paystack webhook signature header
    
    Returns:
        Confirmation response
    """
    try:
        # Get raw request body
        body = await request.body()
        
        # Verify webhook signature
        if x_paystack_signature:
            if not PaymentService.verify_webhook_signature(body, x_paystack_signature):
                logger.warning("Invalid webhook signature")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )
        
        # Parse event data
        event_data = json.loads(body.decode('utf-8'))
        
        # Handle webhook event
        result = await PaymentService.handle_webhook_event(event_data)
        
        logger.info(
            "Webhook processed",
            event=event_data.get("event"),
            status=result.get("status")
        )
        
        return {"status": "success", "message": "Webhook processed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Webhook processing error", error=str(e))
        # Return 200 to prevent Paystack retries for our errors
        return {"status": "error", "message": str(e)}


@router.get("/plans", response_model=Response[dict])
async def get_available_plans():
    """
    Get all available subscription plans with pricing and features
    
    Returns:
        List of available subscription plans
    """
    try:
        plans = SubscriptionPlanService.get_all_plans()
        
        # Format for frontend
        formatted_plans = {}
        for plan_key, plan_data in plans.items():
            formatted_plans[plan_key] = {
                "name": plan_data["name"],
                "price_monthly_usd": plan_data.get("price_monthly_usd"),
                "price_monthly_ghs": plan_data.get("price_monthly_ghs"),
                "trial_days": plan_data.get("trial_days"),
                "limits": plan_data.get("limits", {}),
                "features": plan_data.get("features", {}),
            }
        
        return Response(
            success=True,
            message="Plans retrieved successfully",
            data={"plans": formatted_plans}
        )
        
    except Exception as e:
        logger.error("Error getting plans", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/current", response_model=Response[dict])
async def get_current_subscription(
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Get current subscription details for the user's organization
    
    Args:
        recruiter_id: Current user ID
    
    Returns:
        Current subscription information
    """
    try:
        # Get usage summary (includes subscription info)
        summary = await UsageLimitChecker.get_usage_summary(recruiter_id)
        
        return Response(
            success=True,
            message="Subscription details retrieved successfully",
            data=summary
        )
        
    except Exception as e:
        logger.error("Error getting current subscription", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

