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
from datetime import timedelta
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
        auth_response = db.client.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )
        
        # Create user profile in public.users table
        user_profile = {
            "id": auth_response.user.id,
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
        
        logger.info("User registered", user_id=auth_response.user.id, email=user_data.email)
        
        return Response(
            success=True,
            message="User registered successfully",
            data=response.data[0]
        )
        
    except Exception as e:
        logger.error("Registration error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
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

