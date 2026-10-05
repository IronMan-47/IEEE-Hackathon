from typing import Optional
from agent.voice.models import VoiceTranscript, ConfidenceLevel
from agent.core.logging import logger

class MockSTTProvider:
    def __init__(self):
        self.is_listening = False

    def start_listening(self) -> None:
        self.is_listening = True
        logger.info("MockSTTProvider started listening.")

    def stop_listening(self) -> None:
        self.is_listening = False
        logger.info("MockSTTProvider stopped listening.")

    def transcribe(self, text_input: str, session_id: str, confidence: str = "HIGH") -> Optional[VoiceTranscript]:
        # For mock purposes, we receive text directly rather than bytes
        if not self.is_listening:
            logger.warning("MockSTTProvider: Transcribe called while not listening.")
            
        logger.info(f"MockSTTProvider transcribed: '{text_input}' with confidence {confidence}")
        return VoiceTranscript(
            session_id=session_id,
            text=text_input,
            confidence=ConfidenceLevel(confidence),
            language="en-US"
        )

class MockTTSProvider:
    def speak(self, text: str) -> None:
        logger.info(f"MockTTSProvider playing TTS: {text}")
