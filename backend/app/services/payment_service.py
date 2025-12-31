"""
Payment Service
Handles Paystack payment integration for subscriptions
Supports both card and mobile money (MOMO) payments
"""

from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
import requests
import hmac
import hashlib
from app.config import settings
from app.config_plans import SubscriptionPlanService
from app.database import db
import structlog

logger = structlog.get_logger()


class PaymentService:
    """Service for handling Paystack payments"""
    
    @staticmethod
    def get_paystack_secret_key() -> str:
        """Get Paystack secret key based on mode"""
        mode = getattr(settings, 'paystack_mode', 'test')
        if mode == 'live':
            return getattr(settings, 'paystack_secret_key', '')
        else:
            return getattr(settings, 'paystack_test_secret_key', '')
    
    @staticmethod
    def get_paystack_public_key() -> str:
        """Get Paystack public key based on mode"""
        mode = getattr(settings, 'paystack_mode', 'test')
        if mode == 'live':
            return getattr(settings, 'paystack_public_key', '')
        else:
            return getattr(settings, 'paystack_test_public_key', '')
    
    @staticmethod
    def verify_webhook_signature(payload: bytes, signature: str) -> bool:
        """
        Verify Paystack webhook signature
        
        Args:
            payload: Raw request body as bytes
            signature: X-Paystack-Signature header value
        
        Returns:
            True if signature is valid
        """
        webhook_secret = getattr(settings, 'paystack_webhook_secret', '')
        if not webhook_secret:
            logger.warning("Paystack webhook secret not configured")
            return False
        
        computed_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(computed_signature, signature)
    
    @staticmethod
    async def create_payment_link(
        company_name: str,
        subscription_plan: str,
        email: str,
        amount_ghs: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a Paystack payment link for subscription
        
        Args:
            company_name: Organization company name
            subscription_plan: Plan identifier
            email: Customer email
            amount_ghs: Amount in GHS (if None, uses plan price)
            metadata: Additional metadata to attach
        
        Returns:
            Payment link response from Paystack
        """
        # Get plan price if amount not provided
        if amount_ghs is None:
            amount_ghs = SubscriptionPlanService.get_plan_price(subscription_plan, currency="ghs")
            if amount_ghs is None:
                raise ValueError(f"Plan {subscription_plan} has no price configured")
        
        # Prepare metadata
        payment_metadata = {
            "company_name": company_name,
            "subscription_plan": subscription_plan,
            **(metadata or {})
        }
        
        # Prepare request
        payload = {
            "email": email,
            "amount": int(amount_ghs * 100),  # Paystack amounts are in kobo/pesewas (multiply by 100)
            "currency": "GHS",
            "reference": f"{company_name}_{subscription_plan}_{datetime.utcnow().timestamp()}",
            "metadata": payment_metadata,
            "callback_url": f"{settings.frontend_url}/dashboard/subscription/callback",
            "channels": ["card", "mobile_money"],  # Support both card and MOMO
        }
        
        secret_key = PaymentService.get_paystack_secret_key()
        headers = {
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                "https://api.paystack.co/transaction/initialize",
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("status"):
                logger.info(
                    "Payment link created",
                    company_name=company_name,
                    subscription_plan=subscription_plan,
                    reference=payload["reference"]
                )
                return result
            else:
                raise Exception(result.get("message", "Failed to create payment link"))
                
        except requests.exceptions.RequestException as e:
            logger.error("Paystack API error", error=str(e))
            raise Exception(f"Payment service error: {str(e)}")
    
    @staticmethod
    async def verify_transaction(reference: str) -> Dict[str, Any]:
        """
        Verify a Paystack transaction
        
        Args:
            reference: Transaction reference
        
        Returns:
            Transaction details
        """
        secret_key = PaymentService.get_paystack_secret_key()
        headers = {
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"https://api.paystack.co/transaction/verify/{reference}",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("status"):
                return result
            else:
                raise Exception(result.get("message", "Failed to verify transaction"))
                
        except requests.exceptions.RequestException as e:
            logger.error("Paystack verification error", error=str(e))
            raise Exception(f"Payment verification error: {str(e)}")
    
    @staticmethod
    async def create_subscription(
        customer_code: str,
        plan_code: str,
        authorization_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Paystack subscription
        
        Args:
            customer_code: Paystack customer code
            plan_code: Paystack plan code
            authorization_code: Authorization code for recurring payment
        
        Returns:
            Subscription details
        """
        secret_key = PaymentService.get_paystack_secret_key()
        headers = {
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "customer": customer_code,
            "plan": plan_code,
        }
        
        if authorization_code:
            payload["authorization"] = authorization_code
        
        try:
            response = requests.post(
                "https://api.paystack.co/subscription",
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("status"):
                return result
            else:
                raise Exception(result.get("message", "Failed to create subscription"))
                
        except requests.exceptions.RequestException as e:
            logger.error("Paystack subscription creation error", error=str(e))
            raise Exception(f"Subscription creation error: {str(e)}")
    
    @staticmethod
    async def handle_webhook_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Paystack webhook event
        
        Supported events:
        - charge.success: Payment successful
        - charge.failed: Payment failed
        - subscription.create: Subscription created
        - subscription.disable: Subscription cancelled
        
        Args:
            event_data: Paystack webhook event data
        
        Returns:
            Processing result
        """
        event_type = event_data.get("event")
        data = event_data.get("data", {})
        
        try:
            if event_type == "charge.success":
                return await PaymentService._handle_payment_success(data)
            elif event_type == "charge.failed":
                return await PaymentService._handle_payment_failed(data)
            elif event_type == "subscription.create":
                return await PaymentService._handle_subscription_created(data)
            elif event_type == "subscription.disable":
                return await PaymentService._handle_subscription_cancelled(data)
            else:
                logger.info("Unhandled webhook event", event_type=event_type)
                return {"status": "ignored", "event_type": event_type}
                
        except Exception as e:
            logger.error("Webhook handling error", event_type=event_type, error=str(e))
            raise
    
    @staticmethod
    async def _handle_payment_success(data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment"""
        metadata = data.get("metadata", {})
        company_name = metadata.get("company_name")
        subscription_plan = metadata.get("subscription_plan")
        amount = data.get("amount", 0) / 100  # Convert from kobo/pesewas
        
        if not company_name or not subscription_plan:
            logger.warning("Payment success missing metadata", data=data)
            return {"status": "skipped", "reason": "missing_metadata"}
        
        # Update organization settings
        update_data = {
            "status": "active",
            "subscription_starts_at": datetime.utcnow().isoformat(),
            "last_payment_date": datetime.utcnow().isoformat(),
            "subscription_ends_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Set next payment date (for recurring)
        if data.get("authorization"):
            update_data["next_payment_date"] = (datetime.utcnow() + timedelta(days=30)).isoformat()
        
        try:
            db.service_client.table("organization_settings").update(update_data).eq(
                "company_name", company_name
            ).execute()
            
            logger.info(
                "Payment success processed",
                company_name=company_name,
                subscription_plan=subscription_plan,
                amount=amount
            )
            
            return {"status": "success", "company_name": company_name}
            
        except Exception as e:
            logger.error("Failed to update org settings after payment", error=str(e))
            raise
    
    @staticmethod
    async def _handle_payment_failed(data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment"""
        metadata = data.get("metadata", {})
        company_name = metadata.get("company_name")
        
        if company_name:
            # Don't change status immediately - give grace period
            logger.warning(
                "Payment failed",
                company_name=company_name,
                reason=data.get("gateway_response")
            )
        
        return {"status": "logged", "company_name": company_name}
    
    @staticmethod
    async def _handle_subscription_created(data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription created"""
        customer = data.get("customer", {})
        company_name = customer.get("metadata", {}).get("company_name")
        
        if company_name:
            update_data = {
                "paystack_subscription_code": data.get("subscription_code"),
                "next_payment_date": data.get("next_payment_date"),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            db.service_client.table("organization_settings").update(update_data).eq(
                "company_name", company_name
            ).execute()
        
        return {"status": "success"}
    
    @staticmethod
    async def _handle_subscription_cancelled(data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription cancellation"""
        customer = data.get("customer", {})
        company_name = customer.get("metadata", {}).get("company_name")
        
        if company_name:
            # Pause subscription instead of immediate cancellation
            update_data = {
                "status": "paused",
                "updated_at": datetime.utcnow().isoformat()
            }
            
            db.service_client.table("organization_settings").update(update_data).eq(
                "company_name", company_name
            ).execute()
        
        return {"status": "success"}

