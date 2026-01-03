"""
Authentication API Routes
Handles user authentication and registration
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from app.schemas.auth import Token, UserLogin, UserRegister
from app.schemas.common import Response
from app.models.user import User
from app.database import db
from app.utils.auth import create_access_token, get_current_user, get_current_user_id_unverified
from app.utils.rate_limit import rate_limit_auth
from app.services.usage_limit_checker import UsageLimitChecker
from app.config_plans import SubscriptionPlanService
from datetime import timedelta, datetime
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=Response[User])
@rate_limit_auth()  # Limit: 5 requests per minute per IP
async def register(request: Request, user_data: UserRegister):
    """
    Register a new recruiter user
    
    Args:
        user_data: User registration data
    
    Returns:
        Created user information
    """
    try:
        # Create user in Supabase Auth
        # Supabase handles email confirmation automatically if enabled
        auth_response = db.client.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
        })
        
        # Check if user was created successfully
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account"
            )
        
        user_id = auth_response.user.id
        
        # Create user profile in public.users table
        # Use service_client to bypass RLS during registration (server-side operation)
        user_profile = {
            "id": user_id,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "company_name": user_data.company_name
        }
        
        response = db.service_client.table("users").insert(user_profile).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user profile"
            )
        
        logger.info("User registered", user_id=user_id, email=user_data.email)
        
        # Create subscription settings if company_name is provided
        subscription_plan = user_data.subscription_plan or "free"
        
        # Validate plan
        plan_config = SubscriptionPlanService.get_plan_config(subscription_plan)
        if not plan_config:
            # Invalid plan - default to free
            subscription_plan = "free"
            plan_config = SubscriptionPlanService.get_plan_config("free")
        
        if user_data.company_name:
            try:
                # Set trial end date (14 days from now by default)
                trial_days = plan_config.get("trial_days", 14)
                trial_ends_at = (datetime.utcnow() + timedelta(days=trial_days)).isoformat()
                
                # Assign plan limits and create organization settings
                await UsageLimitChecker.assign_plan_limits(user_data.company_name, subscription_plan)
                
                # Update trial end date
                db.service_client.table("organization_settings").update({
                    "trial_ends_at": trial_ends_at,
                    "status": "trial",
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("company_name", user_data.company_name).execute()
                
                logger.info(
                    "Subscription created for new user",
                    user_id=user_id,
                    company_name=user_data.company_name,
                    subscription_plan=subscription_plan,
                    trial_ends_at=trial_ends_at
                )
            except Exception as e:
                # Log error but don't fail registration
                logger.warning(
                    "Failed to create subscription settings during registration",
                    error=str(e),
                    user_id=user_id,
                    company_name=user_data.company_name
                )
        
        # Default templates will be created lazily when user first accesses templates
        # This ensures registration is fast and templates are created when needed
        
        # Generate and send email verification code
        try:
            from app.services.email_verification_service import EmailVerificationService
            verification_result = await EmailVerificationService.send_verification_code(
                user_id=user_id,
                email=user_data.email,
                full_name=user_data.full_name
            )
            logger.info("Verification code sent", user_id=user_id, email=user_data.email)
        except Exception as e:
            # Log error but don't fail registration - user can request code later
            logger.error("Failed to send verification code during registration", error=str(e), user_id=user_id)
        
        # Return success - user needs to verify email before accessing the site
        message = "Registration successful! Please check your email for a verification code to complete your account setup."
        if subscription_plan != "free":
            message += f" Your {subscription_plan} plan trial will start after email verification."
        
        # Don't include sensitive data in response
        user_data_response = response.data[0].copy()
        user_data_response["email_verified"] = False  # Indicate email not verified yet
        
        return Response(
            success=True,
            message=message,
            data=user_data_response
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        error_message = str(e)
        logger.error("Registration error", error=error_message, email=user_data.email)
        
        # Provide helpful error messages for common issues
        if "already registered" in error_message.lower() or "user already exists" in error_message.lower() or "already been registered" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists"
            )
        elif "password" in error_message.lower() and ("weak" in error_message.lower() or "requirements" in error_message.lower()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet requirements. Please use a stronger password."
            )
        else:
            # Generic error message for security (don't leak internal details)
            # Note: Email confirmation errors are handled by Supabase, not our application
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed. Please check your information and try again."
            )


@router.post("/login", response_model=Response[Token])
@rate_limit_auth()  # Limit: 5 requests per minute per IP (prevents brute force)
async def login(request: Request, credentials: UserLogin):
    """
    Login user and return access token
    
    Args:
        credentials: User login credentials
    
    Returns:
        Access token
    """
    # Log login attempt for debugging CORS/connection issues
    logger.info(
        "Login attempt received",
        email=credentials.email,
        method=request.method,
        origin=request.headers.get("origin"),
        user_agent=request.headers.get("user-agent")[:100] if request.headers.get("user-agent") else None
    )
    try:
        # Authenticate with Supabase
        auth_response = db.client.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password,
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if email is verified
        from app.services.email_verification_service import EmailVerificationService
        from uuid import UUID
        user_id = UUID(auth_response.user.id)
        
        is_verified = EmailVerificationService.is_email_verified(user_id)
        if not is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email address before logging in. Check your email for a verification code."
            )
        
        # Create access token
        access_token_expires = timedelta(hours=24)
        access_token = create_access_token(
            data={"sub": auth_response.user.id},
            expires_delta=access_token_expires
        )
        
        logger.info("User logged in", user_id=auth_response.user.id, email=credentials.email)
        
        return Response(
            success=True,
            message="Login successful",
            data=Token(access_token=access_token, token_type="bearer")
        )
        
    except Exception as e:
        logger.error("Login error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


@router.post("/verify-email", response_model=Response[dict])
@rate_limit_auth()  # Limit verification attempts
async def verify_email(
    request: Request,
    code: str = Body(..., description="6-digit verification code"),
    current_user: dict = Depends(get_current_user)  # Allow unverified users to access this endpoint
):
    """
    Verify email address with verification code
    
    Args:
        code: 6-digit verification code from email
        current_user: Current authenticated user
        
    Returns:
        Verification result
    """
    try:
        from app.services.email_verification_service import EmailVerificationService
        from uuid import UUID
        
        user_id = UUID(current_user["id"])
        
        result = await EmailVerificationService.verify_code(user_id, code)
        
        if result["success"]:
            logger.info("Email verified", user_id=str(user_id))
            return Response(
                success=True,
                message=result.get("message", "Email verified successfully"),
                data=result
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Verification failed")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error verifying email", error=str(e), user_id=current_user.get("id"))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify email. Please try again."
        )


@router.post("/resend-verification", response_model=Response[dict])
@rate_limit_auth()  # Limit resend attempts
async def resend_verification(
    request: Request,
    current_user: dict = Depends(get_current_user)  # Allow unverified users to resend
):
    """
    Resend email verification code
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Resend result
    """
    try:
        from app.services.email_verification_service import EmailVerificationService
        from uuid import UUID
        
        user_id = UUID(current_user["id"])
        
        result = await EmailVerificationService.resend_verification_code(user_id)
        
        if result["success"]:
            logger.info("Verification code resent", user_id=str(user_id))
            return Response(
                success=True,
                message=result.get("message", "Verification code sent successfully"),
                data=result
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to resend verification code")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error resending verification code", error=str(e), user_id=current_user.get("id"))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification code. Please try again."
        )


@router.get("/me", response_model=Response[User])
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information
    
    Args:
        current_user: Current authenticated user (from dependency)
    
    Returns:
        Current user information
    """
    return Response(
        success=True,
        message="User retrieved successfully",
        data=current_user
    )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout current user
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Logout confirmation
    """
    # In a JWT-based system, logout is typically handled client-side
    # by removing the token. If using refresh tokens, you might want
    # to invalidate them here.
    
    logger.info("User logged out", user_id=current_user["id"])
    
    return Response(
        success=True,
        message="Logged out successfully"
    )

