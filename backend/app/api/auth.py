"""
Authentication API Routes
Handles user authentication and registration
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.schemas.auth import Token, UserLogin, UserRegister
from app.schemas.common import Response
from app.models.user import User
from app.database import db
from app.utils.auth import create_access_token, get_current_user
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
        user_profile = {
            "id": user_id,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "company_name": user_data.company_name
        }
        
        response = db.client.table("users").insert(user_profile).execute()
        
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
        
        # Return success - Supabase handles email confirmation automatically
        message = "User registered successfully. Please check your email to confirm your account."
        if subscription_plan != "free":
            message += f" Your {subscription_plan} plan trial has started."
        
        return Response(
            success=True,
            message=message,
            data=response.data[0]
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

