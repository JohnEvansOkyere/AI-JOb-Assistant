"""
Audio Processing Utilities
Helper functions for audio format conversion and validation
"""

import io
from typing import Optional
import structlog

logger = structlog.get_logger()


def validate_audio_format(audio_bytes: bytes, filename: Optional[str] = None) -> bool:
    """
    Validate audio file format
    
    Args:
        audio_bytes: Audio file bytes
        filename: Optional filename for format detection
    
    Returns:
        True if format is valid/supported
    """
    # Check file signature (magic bytes)
    if len(audio_bytes) < 12:
        return False
    
    # WebM/Matroska format: starts with 0x1A 0x45 0xDF 0xA3
    if audio_bytes[:4] == b'\x1a\x45\xdf\xa3':
        return True
    
    # WAV format: starts with "RIFF" followed by "WAVE"
    if audio_bytes[:4] == b'RIFF' and audio_bytes[8:12] == b'WAVE':
        return True
    
    # MP3 format: starts with ID3 tag or MP3 frame sync (0xFF 0xFB or 0xFF 0xF3)
    if audio_bytes[:3] == b'ID3' or audio_bytes[:2] in (b'\xff\xfb', b'\xff\xf3'):
        return True
    
    # MP4/M4A format: starts with ftyp box
    if audio_bytes[4:8] == b'ftyp':
        return True
    
    # Check by filename extension if provided
    if filename:
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if ext in ('webm', 'wav', 'mp3', 'm4a', 'mp4', 'ogg', 'opus'):
            return True
    
    return False


def prepare_audio_for_whisper(audio_bytes: bytes, filename: Optional[str] = None) -> tuple[bytes, str]:
    """
    Prepare audio bytes for Whisper API
    
    Whisper API accepts: mp3, mp4, mpeg, mpga, m4a, wav, webm
    
    Args:
        audio_bytes: Raw audio bytes
        filename: Optional filename for format detection
    
    Returns:
        Tuple of (audio_bytes, file_extension)
    
    Note:
        For now, we pass through the audio as-is and let Whisper handle it.
        If format conversion is needed in the future, we can add ffmpeg here.
    """
    # Validate format
    if not validate_audio_format(audio_bytes, filename):
        logger.warning("Audio format validation failed", filename=filename)
    
    # Determine file extension from filename or file signature
    extension = "webm"  # Default (most common from browser MediaRecorder)
    
    if filename:
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if ext in ('webm', 'wav', 'mp3', 'm4a', 'mp4', 'ogg', 'opus'):
            extension = ext
    else:
        # Try to detect from magic bytes
        if len(audio_bytes) >= 12:
            if audio_bytes[:4] == b'RIFF' and audio_bytes[8:12] == b'WAVE':
                extension = "wav"
            elif audio_bytes[:3] == b'ID3' or audio_bytes[:2] in (b'\xff\xfb', b'\xff\xf3'):
                extension = "mp3"
            elif audio_bytes[4:8] == b'ftyp':
                extension = "m4a"
            elif audio_bytes[:4] == b'\x1a\x45\xdf\xa3':
                extension = "webm"
    
    return audio_bytes, extension

