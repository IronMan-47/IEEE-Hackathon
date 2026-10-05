from typing import Optional, Dict, Any
from agent.voice.models import VoiceSession as VoiceSessionModel, VoiceState, ConfidenceLevel, VoiceTranscript, VoiceCommand, InteractionIntentType
from agent.voice.mock_provider import MockSTTProvider, MockTTSProvider
from agent.runtime.lifecycle import runtime_manager
from agent.core.logging import logger

class VoiceSessionManager:
    def __init__(self):
        self.current_session: Optional[VoiceSessionModel] = None
        self.stt_provider = MockSTTProvider()
        self.tts_provider = MockTTSProvider()

    def start_listening(self) -> VoiceSessionModel:
        if self.current_session and self.current_session.status == VoiceState.LISTENING:
            return self.current_session

        self.current_session = VoiceSessionModel(status=VoiceState.LISTENING)
        self.stt_provider.start_listening()
        
        runtime_manager._emit("VOICE_SESSION_STARTED", {"session_id": self.current_session.session_id})
        runtime_manager._emit("VOICE_LISTENING_STARTED", {"session_id": self.current_session.session_id})
        
        return self.current_session

    def stop_listening(self) -> Optional[VoiceSessionModel]:
        if not self.current_session:
            return None
        
        self.stt_provider.stop_listening()
        self.current_session.status = VoiceState.PROCESSING
        runtime_manager._emit("VOICE_LISTENING_STOPPED", {"session_id": self.current_session.session_id})
        return self.current_session

    def process_speech(self, text: str, confidence: str = "HIGH") -> Dict[str, Any]:
        """
        Simulates receiving a transcript from the STT provider.
        """
        if not self.current_session:
            logger.warning("Voice processing called without an active session.")
            return {"status": "FAILED", "reason": "NO_ACTIVE_SESSION"}

        runtime_manager._emit("VOICE_TRANSCRIPTION_STARTED", {"session_id": self.current_session.session_id})
        
        transcript = self.stt_provider.transcribe(text, self.current_session.session_id, confidence)
        if not transcript:
            self.current_session.status = VoiceState.ERROR
            runtime_manager._emit("VOICE_TRANSCRIPTION_FAILED", {"session_id": self.current_session.session_id})
            return {"status": "FAILED", "reason": "TRANSCRIPTION_FAILED"}
        
        runtime_manager._emit("VOICE_TRANSCRIPTION_COMPLETED", {
            "session_id": self.current_session.session_id,
            "transcript_id": transcript.transcript_id,
            "confidence": transcript.confidence.value
        })

        if transcript.confidence == ConfidenceLevel.LOW:
            self.current_session.status = VoiceState.WAITING_FOR_USER
            runtime_manager._emit("VOICE_CONFIRMATION_REQUIRED", {
                "session_id": self.current_session.session_id,
                "transcript": transcript.text
            })
            # Optionally use TTS
            self.tts_provider.speak("I didn't quite catch that. Could you confirm?")
            return {"status": "CONFIRMATION_REQUIRED", "transcript": transcript.model_dump()}
            
        return self._route_transcript(transcript)

    def _route_transcript(self, transcript: VoiceTranscript) -> Dict[str, Any]:
        from agent.voice.command_router import VoiceCommandRouter
        
        active_task_id = runtime_manager.state.active_task_id
        command = VoiceCommandRouter.route_transcript(transcript, active_task_id)
        
        self.current_session.status = VoiceState.IDLE
        runtime_manager._emit("VOICE_COMMAND_ACCEPTED", {
            "session_id": self.current_session.session_id,
            "command_id": command.command_id,
            "intent": command.interaction_intent.value
        })
        
        # End session after successful routing (push-to-talk completes)
        self._end_session()
        
        return {"status": "ROUTED", "command": command.model_dump()}

    def confirm_transcript(self, transcript_id: str, text: str) -> Dict[str, Any]:
        if not self.current_session or self.current_session.status != VoiceState.WAITING_FOR_USER:
            return {"status": "FAILED", "reason": "INVALID_STATE"}
            
        transcript = VoiceTranscript(
            session_id=self.current_session.session_id,
            text=text,
            confidence=ConfidenceLevel.HIGH, # Confirmed by user
            language=self.current_session.language,
            transcript_id=transcript_id
        )
        return self._route_transcript(transcript)

    def cancel_session(self) -> None:
        if self.current_session:
            self.stt_provider.stop_listening()
            self.current_session.status = VoiceState.STOPPED
            self._end_session()

    def _end_session(self) -> None:
        if self.current_session:
            from datetime import datetime, timezone
            self.current_session.ended_at = datetime.now(timezone.utc).isoformat()
            runtime_manager._emit("VOICE_SESSION_ENDED", {"session_id": self.current_session.session_id})
            self.current_session = None

voice_manager = VoiceSessionManager()
