from typing import Protocol


class TTSProvider(Protocol):
    async def synthesize(self, text: str) -> bytes:
        ...


class ElevenLabsTTS:
    """
    Placeholder for ElevenLabs TTS integration.
    Later this will call ElevenLabs API using the configured voice.
    """

    async def synthesize(self, text: str) -> bytes:
        # TODO: Implement real TTS call to ElevenLabs
        return b""


def get_tts_provider() -> TTSProvider:
    # For now we only support ElevenLabs; later we can add more providers.
    return ElevenLabsTTS()


