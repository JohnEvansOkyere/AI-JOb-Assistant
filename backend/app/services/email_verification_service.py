"""
Email Verification Service
Handles email verification code generation, sending, and validation
"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
import secrets
import structlog
from app.database import db
from app.services.email_service import EmailService
from app.config import settings

logger = structlog.get_logger()


class EmailVerificationService:
    """Service for email verification with OTP codes"""
    
    CODE_LENGTH = 6
    CODE_EXPIRY_MINUTES = 10
    MAX_VERIFICATION_ATTEMPTS = 5
    MAX_CODE_RESEND_ATTEMPTS = 3
    RESEND_COOLDOWN_MINUTES = 1
    
    @staticmethod
    def generate_verification_token() -> str:
        """
        Generate a secure verification token for email link
        
        Returns:
            Secure token string
        """
        # Generate secure token (32 bytes = 256 bits)
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_verification_code() -> str:
        """
        Generate a secure 6-digit verification code
        
        Returns:
            6-digit code as string
        """
        # Generate random 6-digit code (000000 to 999999)
        code = str(secrets.randbelow(1000000)).zfill(6)
        logger.debug("Generated verification code", code_length=len(code))
        return code
    
    @staticmethod
    async def send_verification_code(user_id: UUID, email: str, full_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate and send verification code to user's email
        
        Args:
            user_id: User ID
            email: User email address
            full_name: Optional user full name for personalization
            
        Returns:
            Dictionary with code info (code is NOT included for security)
        """
        try:
            # Generate verification code and token
            code = EmailVerificationService.generate_verification_code()
            token = EmailVerificationService.generate_verification_token()
            
            # Set expiry (10 minutes from now)
            expires_at = datetime.utcnow() + timedelta(minutes=EmailVerificationService.CODE_EXPIRY_MINUTES)
            
            # Store code and token in database (both expire at same time)
            # Handle case where token columns might not exist yet (backward compatibility)
            update_data = {
                "email_verification_code": code,
                "email_verification_code_expires_at": expires_at.isoformat(),
                "email_verification_attempts": 0,  # Reset attempts on new code
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Try to add token columns if they exist
            try:
                update_data["email_verification_token"] = token
                update_data["email_verification_token_expires_at"] = expires_at.isoformat()
            except Exception:
                pass  # Token columns might not exist, but we'll still save the code
            
            try:
                db.service_client.table("users").update(update_data).eq("id", str(user_id)).execute()
            except Exception as db_error:
                error_msg = str(db_error)
                # Check if it's a missing column error for token
                if "email_verification_token" in error_msg and "column" in error_msg.lower():
                    logger.warning(
                        "Token columns not found, using code-only verification",
                        error=error_msg,
                        user_id=str(user_id),
                        hint="Run migration: backend/migrations/025_add_email_verification_token.sql for button/link support"
                    )
                    # Retry without token columns
                    update_data = {
                        "email_verification_code": code,
                        "email_verification_code_expires_at": expires_at.isoformat(),
                        "email_verification_attempts": 0,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    db.service_client.table("users").update(update_data).eq("id", str(user_id)).execute()
                    # Set token to None so email doesn't include button
                    token = None
                elif "email_verification_code" in error_msg or "column" in error_msg.lower():
                    logger.error(
                        "Database migration not run - email verification columns missing",
                        error=error_msg,
                        user_id=str(user_id),
                        hint="Please run migration: backend/migrations/024_add_email_verification.sql"
                    )
                    raise Exception(
                        "Database migration required: Please run the migration file "
                        "backend/migrations/024_add_email_verification.sql in Supabase SQL Editor. "
                        f"Error: {error_msg}"
                    )
                else:
                    raise
            
            logger.info("Verification code and token generated", user_id=str(user_id), expires_at=expires_at.isoformat())
            
            # Send verification email
            await EmailVerificationService._send_verification_email(
                user_id=user_id,
                email=email,
                code=code,
                token=token,
                full_name=full_name
            )
            
            return {
                "success": True,
                "expires_at": expires_at.isoformat(),
                "expires_in_minutes": EmailVerificationService.CODE_EXPIRY_MINUTES
            }
            
        except Exception as e:
            logger.error("Error sending verification code", error=str(e), user_id=str(user_id), exc_info=True)
            raise Exception(f"Failed to send verification code: {str(e)}")
    
    @staticmethod
    async def _send_verification_email(
        user_id: UUID,
        email: str,
        code: str,
        token: str,
        full_name: Optional[str] = None
    ) -> None:
        """
        Send verification email with both code and button link
        
        Args:
            user_id: User ID
            email: User email address
            code: 6-digit verification code
            token: Verification token for link
            full_name: Optional user full name
        """
        try:
            from app.config import settings
            
            # Prepare email content
            display_name = full_name or "there"
            subject = "Verify Your Email - Veloxa Recruit"
            
            # Generate verification link (only if token exists)
            verify_link = None
            if token:
                frontend_url = settings.frontend_url
                verify_link = f"{frontend_url}/verify-email?token={token}"
            
            # Build button section conditionally
            button_section = ""
            if verify_link:
                button_section = f"""
                    <!-- Verify Button -->
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verify_link}" style="display: inline-block; background-color: #2563eb; color: white; padding: 14px 32px; text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: bold;">
                            Verify Email Address
                        </a>
                    </div>
                    
                    <p style="text-align: center; font-size: 14px; color: #6b7280; margin: 15px 0;">
                        Or use the verification code:
                    </p>
                """
            
            body_html = f"""
            <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="background-color: #2563eb; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
                    <h1 style="margin: 0; font-size: 24px;">Verify Your Email</h1>
                </div>
                
                <div style="background-color: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
                    <p style="font-size: 16px; margin-top: 0;">Hello {display_name},</p>
                    
                    <p style="font-size: 16px;">Thank you for signing up for Veloxa Recruit! Please verify your email address to complete your registration.</p>
                    
                    {button_section}
                    
                    <!-- Verification Code -->
                    <div style="background-color: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center; border: 2px dashed #2563eb;">
                        <div style="font-size: 32px; font-weight: bold; letter-spacing: 6px; color: #2563eb; font-family: 'Courier New', monospace;">
                            {code}
                        </div>
                    </div>
                    
                    <p style="font-size: 14px; color: #6b7280; text-align: center; margin-top: 15px;">
                        <strong>⏰ This code will expire in {EmailVerificationService.CODE_EXPIRY_MINUTES} minutes.</strong>
                    </p>
                    
                    <p style="font-size: 14px; color: #6b7280; text-align: center; margin-top: 25px;">
                        If you didn't create an account with Veloxa Recruit, please ignore this email.
                    </p>
                    
                    <div style="margin: 25px 0; padding: 15px; background-color: #fef3c7; border-radius: 6px; border-left: 4px solid #f59e0b;">
                        <p style="margin: 0; font-size: 13px; color: #92400e;">
                            <strong>🔒 Security Tip:</strong> Never share this code or link with anyone. Veloxa Recruit will never ask for your verification code.
                        </p>
                    </div>
                    
                    <p style="font-size: 15px; margin-bottom: 0; margin-top: 25px;">
                        Best regards,<br>
                        <strong>The Veloxa Recruit Team</strong>
                    </p>
                </div>
                
                <div style="text-align: center; margin-top: 20px; padding: 20px; color: #6b7280; font-size: 12px;">
                    <p style="margin: 5px 0;">This is an automated email. Please do not reply to this message.</p>
                    <p style="margin: 5px 0;">If you need assistance, please contact us at hello@veloxarecruit.com</p>
                </div>
            </div>
            """
            
            # Build text version conditionally
            if verify_link:
                text_link_section = f"""Option 1: Click this link to verify:
{verify_link}

Option 2: Use this verification code:
"""
            else:
                text_link_section = "Use this verification code:\n"
            
            body_text = f"""
Hello {display_name},

Thank you for signing up for Veloxa Recruit! Please verify your email address to complete your registration.

{text_link_section}{code}

This code will expire in {EmailVerificationService.CODE_EXPIRY_MINUTES} minutes.

If you didn't create an account with Veloxa Recruit, please ignore this email.

Security Tip: Never share this code or link with anyone. Veloxa Recruit will never ask for your verification code.

Best regards,
The Veloxa Recruit Team

---
This is an automated email. Please do not reply to this message.
If you need assistance, please contact us at hello@veloxarecruit.com
            """
            
            # Send email via EmailService
            await EmailService.send_email(
                recruiter_id=user_id,  # Use user_id as recruiter_id for tracking
                recipient_email=email,
                recipient_name=full_name,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
            )
            
            logger.info("Verification email sent", user_id=str(user_id), email=email)
            
        except Exception as e:
            logger.error("Error sending verification email", error=str(e), user_id=str(user_id), exc_info=True)
            raise
    
    @staticmethod
    async def verify_by_token(token: str) -> Dict[str, Any]:
        """
        Verify email using verification token from link
        
        Args:
            token: Verification token from email link
            
        Returns:
            Dictionary with verification result
        """
        try:
            # Find user by token
            user_response = db.service_client.table("users").select(
                "id",
                "email_verification_token",
                "email_verification_token_expires_at",
                "email_verified_at",
                "email_verification_attempts"
            ).eq("email_verification_token", token).execute()
            
            if not user_response.data:
                return {
                    "success": False,
                    "error": "Invalid verification link. The link may have expired or been used already.",
                    "can_resend": True
                }
            
            user_data = user_response.data[0]
            user_id = UUID(user_data["id"])
            
            # Check if already verified
            if user_data.get("email_verified_at"):
                return {
                    "success": True,
                    "already_verified": True,
                    "message": "Email already verified"
                }
            
            # Check if token expired
            expires_at_str = user_data.get("email_verification_token_expires_at")
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                if datetime.utcnow().replace(tzinfo=None) > expires_at.replace(tzinfo=None):
                    # Token expired - clear it
                    db.service_client.table("users").update({
                        "email_verification_token": None,
                        "email_verification_token_expires_at": None,
                        "email_verification_code": None,
                        "email_verification_code_expires_at": None,
                        "updated_at": datetime.utcnow().isoformat()
                    }).eq("id", str(user_id)).execute()
                    
                    return {
                        "success": False,
                        "error": "Verification link has expired. Please request a new verification email.",
                        "can_resend": True,
                        "expired": True
                    }
            
            # Token is valid - mark email as verified
            verified_at = datetime.utcnow()
            db.service_client.table("users").update({
                "email_verified_at": verified_at.isoformat(),
                "email_verification_token": None,  # Clear token after use
                "email_verification_token_expires_at": None,
                "email_verification_code": None,  # Clear code as well
                "email_verification_code_expires_at": None,
                "email_verification_attempts": 0,
                "updated_at": verified_at.isoformat()
            }).eq("id", str(user_id)).execute()
            
            logger.info("Email verified via token", user_id=str(user_id))
            
            return {
                "success": True,
                "verified_at": verified_at.isoformat(),
                "message": "Email verified successfully",
                "user_id": str(user_id)  # Include user_id for auto-login
            }
            
        except Exception as e:
            logger.error("Error verifying by token", error=str(e), exc_info=True)
            raise Exception(f"Failed to verify email: {str(e)}")
    
    @staticmethod
    async def verify_code(user_id: UUID, code: str) -> Dict[str, Any]:
        """
        Verify the provided code against stored code
        
        Args:
            user_id: User ID
            code: Verification code to check
            
        Returns:
            Dictionary with verification result
        """
        try:
            # Get user's verification data
            user_response = db.service_client.table("users").select(
                "email_verification_code",
                "email_verification_code_expires_at",
                "email_verified_at",
                "email_verification_attempts"
            ).eq("id", str(user_id)).execute()
            
            if not user_response.data:
                raise Exception("User not found")
            
            user_data = user_response.data[0]
            
            # Check if already verified
            if user_data.get("email_verified_at"):
                return {
                    "success": True,
                    "already_verified": True,
                    "message": "Email already verified"
                }
            
            # Check if code exists
            stored_code = user_data.get("email_verification_code")
            if not stored_code:
                return {
                    "success": False,
                    "error": "No verification code found. Please request a new code.",
                    "can_resend": True
                }
            
            # Check if code expired
            expires_at_str = user_data.get("email_verification_code_expires_at")
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                if datetime.utcnow().replace(tzinfo=None) > expires_at.replace(tzinfo=None):
                    # Code expired - clear it and token
                    db.service_client.table("users").update({
                        "email_verification_code": None,
                        "email_verification_code_expires_at": None,
                        "email_verification_token": None,
                        "email_verification_token_expires_at": None,
                        "updated_at": datetime.utcnow().isoformat()
                    }).eq("id", str(user_id)).execute()
                    
                    return {
                        "success": False,
                        "error": "Verification code has expired. Please request a new code.",
                        "can_resend": True,
                        "expired": True
                    }
            
            # Check attempts
            attempts = user_data.get("email_verification_attempts", 0)
            if attempts >= EmailVerificationService.MAX_VERIFICATION_ATTEMPTS:
                return {
                    "success": False,
                    "error": f"Too many failed attempts. Please request a new code.",
                    "can_resend": True,
                    "max_attempts_reached": True
                }
            
            # Verify code (case-insensitive, strip whitespace)
            code_clean = code.strip()
            stored_code_clean = stored_code.strip()
            
            if code_clean != stored_code_clean:
                # Increment attempts
                new_attempts = attempts + 1
                db.service_client.table("users").update({
                    "email_verification_attempts": new_attempts,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", str(user_id)).execute()
                
                remaining_attempts = EmailVerificationService.MAX_VERIFICATION_ATTEMPTS - new_attempts
                
                return {
                    "success": False,
                    "error": f"Invalid verification code. {remaining_attempts} attempt(s) remaining.",
                    "remaining_attempts": remaining_attempts,
                    "can_resend": remaining_attempts <= 2  # Allow resend if low on attempts
                }
            
            # Code is valid - mark email as verified
            verified_at = datetime.utcnow()
            db.service_client.table("users").update({
                "email_verified_at": verified_at.isoformat(),
                "email_verification_code": None,  # Clear code after successful verification
                "email_verification_code_expires_at": None,
                "email_verification_token": None,  # Clear token after successful verification
                "email_verification_token_expires_at": None,
                "email_verification_attempts": 0,  # Reset attempts
                "updated_at": verified_at.isoformat()
            }).eq("id", str(user_id)).execute()
            
            logger.info("Email verified successfully", user_id=str(user_id))
            
            return {
                "success": True,
                "verified_at": verified_at.isoformat(),
                "message": "Email verified successfully",
                "user_id": str(user_id)  # Include user_id for auto-login
            }
            
        except Exception as e:
            logger.error("Error verifying code", error=str(e), user_id=str(user_id), exc_info=True)
            raise Exception(f"Failed to verify code: {str(e)}")
    
    @staticmethod
    async def resend_verification_code(user_id: UUID) -> Dict[str, Any]:
        """
        Resend verification code (with rate limiting)
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with result
        """
        try:
            # Get user data
            user_response = db.service_client.table("users").select(
                "email",
                "full_name",
                "email_verification_code_expires_at",
                "email_verified_at"
            ).eq("id", str(user_id)).execute()
            
            if not user_response.data:
                raise Exception("User not found")
            
            user_data = user_response.data[0]
            
            # Check if already verified
            if user_data.get("email_verified_at"):
                return {
                    "success": False,
                    "error": "Email is already verified",
                    "already_verified": True
                }
            
            # Check cooldown (prevent spam)
            expires_at_str = user_data.get("email_verification_code_expires_at")
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                cooldown_until = expires_at.replace(tzinfo=None) - timedelta(
                    minutes=EmailVerificationService.CODE_EXPIRY_MINUTES - EmailVerificationService.RESEND_COOLDOWN_MINUTES
                )
                
                if datetime.utcnow().replace(tzinfo=None) < cooldown_until:
                    wait_seconds = int((cooldown_until - datetime.utcnow().replace(tzinfo=None)).total_seconds())
                    return {
                        "success": False,
                        "error": f"Please wait {wait_seconds} seconds before requesting a new code.",
                        "wait_seconds": wait_seconds,
                        "can_retry_after": cooldown_until.isoformat()
                    }
            
            # Resend code
            result = await EmailVerificationService.send_verification_code(
                user_id=user_id,
                email=user_data["email"],
                full_name=user_data.get("full_name")
            )
            
            return {
                "success": True,
                "message": "Verification code sent successfully",
                "expires_at": result["expires_at"],
                "expires_in_minutes": result["expires_in_minutes"]
            }
            
        except Exception as e:
            logger.error("Error resending verification code", error=str(e), user_id=str(user_id), exc_info=True)
            raise Exception(f"Failed to resend verification code: {str(e)}")
    
    @staticmethod
    def is_email_verified(user_id: UUID) -> bool:
        """
        Check if user's email is verified
        
        Args:
            user_id: User ID
            
        Returns:
            True if verified, False otherwise
        """
        try:
            user_response = db.service_client.table("users").select("email_verified_at").eq("id", str(user_id)).execute()
            
            if not user_response.data:
                return False
            
            return user_response.data[0].get("email_verified_at") is not None
            
        except Exception as e:
            logger.error("Error checking email verification status", error=str(e), user_id=str(user_id))
            return False

