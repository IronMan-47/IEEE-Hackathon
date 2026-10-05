from typing import Protocol, Optional
from agent.voice.models import VoiceTranscript, ConfidenceLevel

class STTProvider(Protocol):
    def start_listening(self) -> None:
        ...

    def stop_listening(self) -> None:
        ...

    def transcribe(self, audio_data: bytes, session_id: str) -> Optional[VoiceTranscript]:
        ...

class TTSProvider(Protocol):
    def speak(self, text: str) -> None:
        ...
