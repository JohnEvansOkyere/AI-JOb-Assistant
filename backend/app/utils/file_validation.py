"""
File Upload Validation Utilities
Provides secure file upload validation including size limits, type checking, and filename sanitization
"""

import os
import re
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException, status
import structlog

logger = structlog.get_logger()

# File size limits (in bytes)
MAX_CV_FILE_SIZE = 10 * 1024 * 1024  # 10 MB for CVs
MAX_LOGO_FILE_SIZE = 5 * 1024 * 1024  # 5 MB for logos
MAX_OFFER_LETTER_SIZE = 10 * 1024 * 1024  # 10 MB for offer letters

# Allowed file types
ALLOWED_CV_TYPES = {
    "application/pdf": [".pdf"],
    "application/msword": [".doc"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    "text/plain": [".txt"],
}

ALLOWED_IMAGE_TYPES = {
    "image/png": [".png"],
    "image/jpeg": [".jpg", ".jpeg"],
    "image/gif": [".gif"],
    "image/webp": [".webp"],
    "image/svg+xml": [".svg"],
}

ALLOWED_PDF_TYPES = {
    "application/pdf": [".pdf"],
}


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and other security issues
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for storage
    """
    if not filename:
        return "file"
    
    # Remove path components (prevent directory traversal)
    filename = os.path.basename(filename)
    
    # Remove any null bytes
    filename = filename.replace("\x00", "")
    
    # Replace dangerous characters with underscore
    # Allow: alphanumeric, dots, hyphens, underscores
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = "file"
    
    # Limit filename length (max 255 chars for most filesystems)
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext
    
    return filename


def validate_file_size(file_size: int, max_size: int, file_type: str = "file") -> None:
    """
    Validate file size against maximum allowed size
    
    Args:
        file_size: File size in bytes
        max_size: Maximum allowed size in bytes
        file_type: Type of file for error message
        
    Raises:
        HTTPException: If file size exceeds limit
    """
    if file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"{file_type} file too large. Maximum size is {max_size_mb:.1f} MB"
        )


def validate_file_type(
    mime_type: Optional[str],
    filename: str,
    allowed_types: dict,
    file_type: str = "file"
) -> Tuple[str, str]:
    """
    Validate file MIME type and extension
    
    Args:
        mime_type: MIME type from upload
        filename: Original filename
        allowed_types: Dictionary of allowed MIME types and extensions
        file_type: Type of file for error message
        
    Returns:
        Tuple of (validated_mime_type, file_extension)
        
    Raises:
        HTTPException: If file type is not allowed
    """
    # Get file extension
    _, ext = os.path.splitext(filename.lower())
    
    # If no MIME type provided, try to infer from extension
    if not mime_type:
        for mime, exts in allowed_types.items():
            if ext in exts:
                mime_type = mime
                break
    
    if not mime_type:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type not recognized. Please upload a supported {file_type} format."
        )
    
    # Check if MIME type is allowed
    if mime_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{mime_type}' not allowed for {file_type}. Allowed types: {', '.join(allowed_types.keys())}"
        )
    
    # Verify extension matches MIME type
    allowed_exts = allowed_types.get(mime_type, [])
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File extension '{ext}' does not match file type '{mime_type}'"
        )
    
    return mime_type, ext


def validate_cv_file(file: UploadFile) -> Tuple[str, int, str]:
    """
    Validate CV file upload
    
    Args:
        file: Uploaded file
        
    Returns:
        Tuple of (sanitized_filename, expected_file_size, validated_mime_type)
        Note: expected_file_size may be 0 if file.size is not available
        
    Raises:
        HTTPException: If validation fails
    """
    # Sanitize filename
    safe_filename = sanitize_filename(file.filename or "cv.pdf")
    
    # Validate file type first
    mime_type, _ = validate_file_type(
        file.content_type,
        safe_filename,
        ALLOWED_CV_TYPES,
        "CV"
    )
    
    # Check file size if available
    expected_file_size = 0
    if hasattr(file, 'size') and file.size:
        expected_file_size = file.size
        validate_file_size(expected_file_size, MAX_CV_FILE_SIZE, "CV")
    
    return safe_filename, expected_file_size, mime_type


def validate_image_file(file: UploadFile) -> Tuple[str, int, str]:
    """
    Validate image file upload (for logos, etc.)
    
    Args:
        file: Uploaded file
        
    Returns:
        Tuple of (sanitized_filename, expected_file_size, validated_mime_type)
        Note: expected_file_size may be 0 if file.size is not available
        
    Raises:
        HTTPException: If validation fails
    """
    safe_filename = sanitize_filename(file.filename or "image.png")
    
    # Validate file type first
    mime_type, _ = validate_file_type(
        file.content_type,
        safe_filename,
        ALLOWED_IMAGE_TYPES,
        "Image"
    )
    
    # Check file size if available
    expected_file_size = 0
    if hasattr(file, 'size') and file.size:
        expected_file_size = file.size
        validate_file_size(expected_file_size, MAX_LOGO_FILE_SIZE, "Image")
    
    return safe_filename, expected_file_size, mime_type


def validate_pdf_file(file: UploadFile) -> Tuple[str, int, str]:
    """
    Validate PDF file upload (for offer letters, etc.)
    
    Args:
        file: Uploaded file
        
    Returns:
        Tuple of (sanitized_filename, expected_file_size, validated_mime_type)
        Note: expected_file_size may be 0 if file.size is not available
        
    Raises:
        HTTPException: If validation fails
    """
    safe_filename = sanitize_filename(file.filename or "document.pdf")
    
    # Validate file type first
    mime_type, _ = validate_file_type(
        file.content_type,
        safe_filename,
        ALLOWED_PDF_TYPES,
        "PDF"
    )
    
    # Check file size if available
    expected_file_size = 0
    if hasattr(file, 'size') and file.size:
        expected_file_size = file.size
        validate_file_size(expected_file_size, MAX_OFFER_LETTER_SIZE, "PDF")
    
    return safe_filename, expected_file_size, mime_type

