"""
Authentication API Routes
Handles user authentication and registration
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from typing import Optional
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
        # Check if user already exists in public.users table
        existing_user = db.service_client.table("users").select("id, email").eq("email", user_data.email).execute()
        
        if existing_user.data:
            # User exists in public.users - already registered
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists"
            )
        
        # Create user in Supabase Auth
        # Disable Supabase's email confirmation (we use custom verification)
        auth_response = db.client.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "email_redirect_to": None  # Disable email confirmation redirect
            }
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
            # Log detailed error
            error_message = str(e)
            logger.error(
                "Failed to send verification code during registration",
                error=error_message,
                user_id=user_id,
                email=user_data.email,
                exc_info=True
            )
            
            # Check if it's a migration issue
            if "migration" in error_message.lower() or "column" in error_message.lower():
                # Don't fail registration, but log clearly
                logger.warning(
                    "Registration completed but email verification requires database migration",
                    user_id=user_id,
                    migration_file="backend/migrations/024_add_email_verification.sql"
                )
            elif "email service not configured" in error_message.lower() or "resend" in error_message.lower() or "smtp" in error_message.lower():
                # Email service configuration issue
                logger.warning(
                    "Registration completed but email verification requires email service configuration",
                    user_id=user_id,
                    hint="Configure RESEND_API_KEY or SMTP settings"
                )
            # User can request code later via resend endpoint
        
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
        error_type = type(e).__name__
        logger.error(
            "Registration error",
            error=error_message,
            error_type=error_type,
            email=user_data.email,
            exc_info=True
        )
        
        # Check for DNS/network errors first
        if "name resolution" in error_message.lower() or "temporary failure" in error_message.lower() or "[errno -3]" in error_message.lower():
            logger.error(
                "DNS/Network connection error during registration",
                error=error_message,
                hint="Check network connection and Supabase URL configuration"
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to connect to the server. Please check your network connection and try again."
            )
        
        # Check for connection timeout errors
        if "timeout" in error_message.lower() or "connection" in error_message.lower():
            logger.error(
                "Connection timeout during registration",
                error=error_message
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Connection timeout. Please try again in a moment."
            )
        
        # Provide helpful error messages for common issues
        if "already registered" in error_message.lower() or "user already exists" in error_message.lower() or "already been registered" in error_message.lower() or "email address is already registered" in error_message.lower():
            # User exists in Supabase Auth (auth.users) - check if it's an orphaned account
            existing_user_check = db.service_client.table("users").select("id").eq("email", user_data.email).execute()
            
            if not existing_user_check.data:
                # Orphaned account - exists in auth.users but not in public.users
                logger.warning(
                    "Orphaned account detected",
                    email=user_data.email,
                    hint="User exists in auth.users but not in public.users. Delete from Supabase Dashboard → Authentication → Users"
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email exists in our authentication system. If you previously deleted your account, it may still exist in our auth system. Please delete it from Supabase Dashboard: Authentication → Users, or contact support."
                )
            else:
                # User exists in both tables - normal case
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
                detail="Please check your email for confirmation"
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
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 403 for unverified email)
        raise
    except Exception as e:
        # Log detailed error information
        error_message = str(e)
        error_type = type(e).__name__
        
        # Check if it's a Supabase AuthApiError (common case)
        if hasattr(e, 'message'):
            error_message = e.message
        elif hasattr(e, 'args') and len(e.args) > 0:
            error_message = str(e.args[0])
        
        logger.error(
            "Login error",
            error=error_message,
            error_type=error_type,
            email=credentials.email,
            exc_info=True
        )
        
        # Check for specific Supabase error messages
        error_lower = error_message.lower()
        
        # Supabase might require email confirmation
        if "email not confirmed" in error_lower or "email_not_confirmed" in error_lower:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please check your email for confirmation"
            )
        elif "invalid" in error_lower and ("credentials" in error_lower or "password" in error_lower or "login" in error_lower):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        else:
            # Generic error for security (don't leak internal details)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )


@router.post("/verify-email", response_model=Response[dict])
@rate_limit_auth()  # Limit verification attempts
async def verify_email(
    request: Request,
    code: str = Body(..., description="6-digit verification code"),
    email: Optional[str] = Body(None, description="User email (required if not authenticated)")
):
    """
    Verify email address with verification code and auto-login user
    Can be called with or without authentication (if email is provided)
    
    Args:
        code: 6-digit verification code from email
        email: User email (required if not authenticated via token)
        
    Returns:
        Verification result with access token (auto-login)
    """
    try:
        from app.services.email_verification_service import EmailVerificationService
        from uuid import UUID
        
        # Try to get authenticated user first (optional)
        user_id = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.replace("Bearer ", "")
                from jose import jwt
                from jose.exceptions import JWTError
                from app.config import settings
                payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
                user_id_str = payload.get("sub")
                if user_id_str:
                    user_id = UUID(user_id_str)
            except (JWTError, Exception):
                pass  # If auth fails, fall back to email lookup
        
        # If not authenticated, use email to find user
        if not user_id:
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email is required when not authenticated"
                )
            # Find user by email
            user_response = db.service_client.table("users").select("id").eq("email", email).execute()
            if not user_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            user_id = UUID(user_response.data[0]["id"])
        
        result = await EmailVerificationService.verify_code(user_id, code)
        
        if result["success"]:
            logger.info("Email verified", user_id=str(user_id))
            
            # Auto-login: Generate access token for the user
            access_token_expires = timedelta(hours=24)
            access_token = create_access_token(
                data={"sub": str(user_id)},
                expires_delta=access_token_expires
            )
            
            return Response(
                success=True,
                message=result.get("message", "Email verified successfully"),
                data={
                    **result,
                    "access_token": access_token,
                    "token_type": "bearer"
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Verification failed")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error verifying email", error=str(e), email=email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify email. Please try again."
        )


@router.get("/verify-email-link/{token}", response_model=Response[dict])
async def verify_email_link(
    request: Request,
    token: str
):
    """
    Verify email using token from email link and auto-login user (public endpoint, no auth required)
    
    Args:
        token: Verification token from email link
        
    Returns:
        Verification result with access token (auto-login)
    """
    try:
        from app.services.email_verification_service import EmailVerificationService
        from uuid import UUID
        
        result = await EmailVerificationService.verify_by_token(token)
        
        if result["success"]:
            logger.info("Email verified via link", token_preview=token[:10] + "...")
            
            # Get user ID from the result or database
            # The verify_by_token method should return user_id in the result
            user_id = None
            if "user_id" in result:
                user_id = UUID(result["user_id"])
            else:
                # Fallback: find user by token (should still exist briefly)
                user_response = db.service_client.table("users").select("id").eq("email_verification_token", token).execute()
                if user_response.data:
                    user_id = UUID(user_response.data[0]["id"])
            
            if user_id:
                # Auto-login: Generate access token for the user
                access_token_expires = timedelta(hours=24)
                access_token = create_access_token(
                    data={"sub": str(user_id)},
                    expires_delta=access_token_expires
                )
                
                return Response(
                    success=True,
                    message=result.get("message", "Email verified successfully"),
                    data={
                        **result,
                        "access_token": access_token,
                        "token_type": "bearer"
                    }
                )
            else:
                # User verified but couldn't get user_id (shouldn't happen)
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
        logger.error("Error verifying email via link", error=str(e))
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

