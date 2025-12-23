"""
Tests for file validation utilities
"""

import pytest
from fastapi import HTTPException, status, UploadFile
from io import BytesIO
from unittest.mock import MagicMock, Mock

from app.utils.file_validation import (
    sanitize_filename,
    validate_file_size,
    validate_file_type,
    validate_cv_file,
    validate_image_file,
    validate_pdf_file,
    MAX_CV_FILE_SIZE,
    MAX_LOGO_FILE_SIZE,
    MAX_OFFER_LETTER_SIZE,
    ALLOWED_CV_TYPES,
    ALLOWED_IMAGE_TYPES,
    ALLOWED_PDF_TYPES
)


@pytest.mark.unit
@pytest.mark.utils
@pytest.mark.file_upload
class TestSanitizeFilename:
    """Tests for sanitize_filename function"""
    
    def test_removes_path_components(self):
        """Test that path traversal attempts are prevented"""
        malicious = "../../../etc/passwd"
        result = sanitize_filename(malicious)
        assert "../" not in result
        assert "passwd" in result or "file" == result
    
    def test_removes_dangerous_characters(self):
        """Test that dangerous characters are removed"""
        dangerous = "file<>:\"|?*name.pdf"
        result = sanitize_filename(dangerous)
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result
        assert "|" not in result
        assert "?" not in result
        assert "*" not in result
    
    def test_removes_null_bytes(self):
        """Test that null bytes are removed"""
        filename = "file\x00name.pdf"
        result = sanitize_filename(filename)
        assert "\x00" not in result
    
    def test_strips_dots_and_spaces(self):
        """Test that leading/trailing dots and spaces are stripped"""
        filename = "...file name...."
        result = sanitize_filename(filename)
        assert not result.startswith(".")
        assert not result.endswith(".")
    
    def test_handles_empty_string(self):
        """Test that empty string returns 'file'"""
        result = sanitize_filename("")
        assert result == "file"
    
    def test_handles_none(self):
        """Test that None returns 'file'"""
        result = sanitize_filename(None)
        assert result == "file"
    
    def test_limits_filename_length(self):
        """Test that filename length is limited to 255 characters"""
        long_name = "a" * 300 + ".pdf"
        result = sanitize_filename(long_name)
        assert len(result) <= 255
    
    def test_preserves_safe_filename(self):
        """Test that safe filenames are preserved"""
        safe = "my_resume-2024.pdf"
        result = sanitize_filename(safe)
        assert result == safe
    
    def test_allows_unicode_characters(self):
        """Test that unicode characters are handled"""
        unicode_name = "résumé-中文.pdf"
        result = sanitize_filename(unicode_name)
        # Should sanitize but not break
        assert len(result) > 0


@pytest.mark.unit
@pytest.mark.utils
@pytest.mark.file_upload
class TestValidateFileSize:
    """Tests for validate_file_size function"""
    
    def test_valid_size_passes(self):
        """Test that valid file sizes pass"""
        validate_file_size(1024, MAX_CV_FILE_SIZE, "CV")
        validate_file_size(MAX_CV_FILE_SIZE, MAX_CV_FILE_SIZE, "CV")
    
    def test_file_too_large_raises_exception(self):
        """Test that files exceeding limit raise HTTPException"""
        with pytest.raises(HTTPException) as exc_info:
            validate_file_size(MAX_CV_FILE_SIZE + 1, MAX_CV_FILE_SIZE, "CV")
        
        assert exc_info.value.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        assert "too large" in exc_info.value.detail.lower()
    
    def test_error_message_contains_file_type(self):
        """Test that error message contains file type"""
        with pytest.raises(HTTPException) as exc_info:
            validate_file_size(MAX_CV_FILE_SIZE + 1, MAX_CV_FILE_SIZE, "CV")
        
        assert "CV" in exc_info.value.detail
    
    def test_zero_size_passes(self):
        """Test that zero size passes"""
        validate_file_size(0, MAX_CV_FILE_SIZE, "File")


@pytest.mark.unit
@pytest.mark.utils
@pytest.mark.file_upload
class TestValidateFileType:
    """Tests for validate_file_type function"""
    
    def test_valid_mime_type_passes(self):
        """Test that valid MIME types pass"""
        mime_type, ext = validate_file_type(
            "application/pdf",
            "document.pdf",
            ALLOWED_PDF_TYPES,
            "PDF"
        )
        assert mime_type == "application/pdf"
        assert ext == ".pdf"
    
    def test_invalid_mime_type_raises_exception(self):
        """Test that invalid MIME types raise HTTPException"""
        with pytest.raises(HTTPException) as exc_info:
            validate_file_type(
                "application/exe",
                "file.exe",
                ALLOWED_PDF_TYPES,
                "PDF"
            )
        
        assert exc_info.value.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    
    def test_infers_mime_from_extension(self):
        """Test that MIME type is inferred from extension if not provided"""
        mime_type, ext = validate_file_type(
            None,
            "document.pdf",
            ALLOWED_PDF_TYPES,
            "PDF"
        )
        assert mime_type == "application/pdf"
        assert ext == ".pdf"
    
    def test_mismatched_extension_raises_exception(self):
        """Test that mismatched extension raises HTTPException"""
        with pytest.raises(HTTPException) as exc_info:
            validate_file_type(
                "application/pdf",
                "file.jpg",
                ALLOWED_PDF_TYPES,
                "PDF"
            )
        
        assert exc_info.value.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    
    def test_case_insensitive_extension(self):
        """Test that extension matching is case insensitive"""
        mime_type, ext = validate_file_type(
            "application/pdf",
            "document.PDF",
            ALLOWED_PDF_TYPES,
            "PDF"
        )
        assert ext == ".pdf"


def _create_upload_file_mock(filename: str, content: bytes, content_type: str, size: int = None):
    """Helper to create a mock UploadFile with proper attributes"""
    file_mock = Mock(spec=UploadFile)
    file_mock.filename = filename
    file_mock.file = BytesIO(content)
    file_mock.content_type = content_type
    file_mock.size = size if size is not None else len(content)
    file_mock.read = Mock(return_value=content)
    file_mock.seek = Mock()
    file_mock.close = Mock()
    return file_mock


@pytest.mark.unit
@pytest.mark.utils
@pytest.mark.file_upload
class TestValidateCVFile:
    """Tests for validate_cv_file function"""
    
    def test_valid_pdf_cv_passes(self):
        """Test that valid PDF CV passes"""
        file = _create_upload_file_mock(
            filename="resume.pdf",
            content=b"PDF content",
            content_type="application/pdf",
            size=1024
        )
        
        filename, size, mime_type = validate_cv_file(file)
        assert filename == "resume.pdf"
        assert size == 1024
        assert mime_type == "application/pdf"
    
    def test_valid_docx_cv_passes(self):
        """Test that valid DOCX CV passes"""
        file = _create_upload_file_mock(
            filename="resume.docx",
            content=b"DOCX content",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            size=2048
        )
        
        filename, size, mime_type = validate_cv_file(file)
        assert ".docx" in filename.lower()
        assert size == 2048
    
    def test_valid_txt_cv_passes(self):
        """Test that valid TXT CV passes"""
        file = _create_upload_file_mock(
            filename="resume.txt",
            content=b"Text content",
            content_type="text/plain",
            size=512
        )
        
        filename, size, mime_type = validate_cv_file(file)
        assert ".txt" in filename.lower()
        assert mime_type == "text/plain"
    
    def test_invalid_file_type_raises_exception(self):
        """Test that invalid file type raises HTTPException"""
        file = _create_upload_file_mock(
            filename="resume.exe",
            content=b"Executable content",
            content_type="application/x-msdownload",
            size=1024
        )
        
        with pytest.raises(HTTPException) as exc_info:
            validate_cv_file(file)
        
        assert exc_info.value.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    
    def test_file_too_large_raises_exception(self):
        """Test that file exceeding size limit raises HTTPException"""
        file = _create_upload_file_mock(
            filename="resume.pdf",
            content=b"Large content",
            content_type="application/pdf",
            size=MAX_CV_FILE_SIZE + 1
        )
        
        with pytest.raises(HTTPException) as exc_info:
            validate_cv_file(file)
        
        assert exc_info.value.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    
    def test_sanitizes_filename(self):
        """Test that filename is sanitized"""
        file = _create_upload_file_mock(
            filename="../../../etc/passwd.pdf",
            content=b"PDF content",
            content_type="application/pdf",
            size=1024
        )
        
        filename, _, _ = validate_cv_file(file)
        assert "../" not in filename
    
    def test_handles_missing_size(self):
        """Test that missing size attribute is handled"""
        file = _create_upload_file_mock(
            filename="resume.pdf",
            content=b"PDF content",
            content_type="application/pdf",
            size=None  # Simulate missing size
        )
        # Remove size attribute to test missing size handling
        delattr(file, 'size')
        
        filename, size, mime_type = validate_cv_file(file)
        assert size == 0  # Should return 0 when size is not available
        assert mime_type == "application/pdf"


@pytest.mark.unit
@pytest.mark.utils
@pytest.mark.file_upload
class TestValidateImageFile:
    """Tests for validate_image_file function"""
    
    def test_valid_png_passes(self):
        """Test that valid PNG passes"""
        file = _create_upload_file_mock(
            filename="logo.png",
            content=b"PNG content",
            content_type="image/png",
            size=1024
        )
        
        filename, size, mime_type = validate_image_file(file)
        assert ".png" in filename.lower()
        assert mime_type == "image/png"
    
    def test_valid_jpeg_passes(self):
        """Test that valid JPEG passes"""
        file = _create_upload_file_mock(
            filename="logo.jpg",
            content=b"JPEG content",
            content_type="image/jpeg",
            size=2048
        )
        
        filename, size, mime_type = validate_image_file(file)
        assert mime_type == "image/jpeg"
    
    def test_file_too_large_raises_exception(self):
        """Test that file exceeding size limit raises HTTPException"""
        file = _create_upload_file_mock(
            filename="logo.png",
            content=b"Large content",
            content_type="image/png",
            size=MAX_LOGO_FILE_SIZE + 1
        )
        
        with pytest.raises(HTTPException) as exc_info:
            validate_image_file(file)
        
        assert exc_info.value.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    
    def test_invalid_file_type_raises_exception(self):
        """Test that invalid file type raises HTTPException"""
        file = _create_upload_file_mock(
            filename="logo.pdf",
            content=b"PDF content",
            content_type="application/pdf",
            size=1024
        )
        
        with pytest.raises(HTTPException) as exc_info:
            validate_image_file(file)
        
        assert exc_info.value.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE


@pytest.mark.unit
@pytest.mark.utils
@pytest.mark.file_upload
class TestValidatePDFFile:
    """Tests for validate_pdf_file function"""
    
    def test_valid_pdf_passes(self):
        """Test that valid PDF passes"""
        file = _create_upload_file_mock(
            filename="document.pdf",
            content=b"PDF content",
            content_type="application/pdf",
            size=1024
        )
        
        filename, size, mime_type = validate_pdf_file(file)
        assert ".pdf" in filename.lower()
        assert mime_type == "application/pdf"
    
    def test_file_too_large_raises_exception(self):
        """Test that file exceeding size limit raises HTTPException"""
        file = _create_upload_file_mock(
            filename="document.pdf",
            content=b"Large content",
            content_type="application/pdf",
            size=MAX_OFFER_LETTER_SIZE + 1
        )
        
        with pytest.raises(HTTPException) as exc_info:
            validate_pdf_file(file)
        
        assert exc_info.value.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    
    def test_invalid_file_type_raises_exception(self):
        """Test that invalid file type raises HTTPException"""
        file = _create_upload_file_mock(
            filename="document.jpg",
            content=b"JPEG content",
            content_type="image/jpeg",
            size=1024
        )
        
        with pytest.raises(HTTPException) as exc_info:
            validate_pdf_file(file)
        
        assert exc_info.value.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE

