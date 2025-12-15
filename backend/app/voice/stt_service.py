from typing import Protocol, Optional


class STTProvider(Protocol):
    async def transcribe_chunk(self, audio_bytes: bytes, language: Optional[str] = None) -> str:
        ...


class WhisperSTT:
    """
    Placeholder for Whisper STT integration.
    In later iterations this will call OpenAI Whisper or another STT provider.
    """

    async def transcribe_chunk(self, audio_bytes: bytes, language: Optional[str] = None) -> str:
        # TODO: Implement real STT using Whisper API
        return ""


class DeepgramSTT:
    """
    Placeholder for Deepgram STT integration.
    """

    async def transcribe_chunk(self, audio_bytes: bytes, language: Optional[str] = None) -> str:
        # TODO: Implement real STT using Deepgram API
        return ""


def get_stt_provider(provider_name: str) -> STTProvider:
    if provider_name.lower() == "deepgram":
        return DeepgramSTT()
    # Default to Whisper
    return WhisperSTT()


