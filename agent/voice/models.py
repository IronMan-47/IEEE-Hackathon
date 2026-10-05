from enum import Enum
from typing import Optional
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field

class VoiceState(str, Enum):
    DISABLED = "DISABLED"
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    ERROR = "ERROR"
    STOPPED = "STOPPED"

class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class InteractionIntentType(str, Enum):
    NEW_REQUEST = "NEW_REQUEST"
    TASK_INTERACTION = "TASK_INTERACTION"
    EXPLANATION_REQUEST = "EXPLANATION_REQUEST"
    CORRECTION = "CORRECTION"
    CONTROL_COMMAND = "CONTROL_COMMAND"
    UNKNOWN = "UNKNOWN"

class VoiceSession(BaseModel):
    session_id: str = Field(default_factory=lambda: f"vs_{uuid.uuid4().hex[:8]}")
    status: VoiceState = VoiceState.IDLE
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    ended_at: Optional[str] = None
    input_mode: str = "PUSH_TO_TALK"
    language: str = "en-US"

class VoiceTranscript(BaseModel):
    transcript_id: str = Field(default_factory=lambda: f"vt_{uuid.uuid4().hex[:8]}")
    session_id: str
    text: str
    confidence: ConfidenceLevel
    language: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = "STT_PROVIDER"

class VoiceCommand(BaseModel):
    command_id: str = Field(default_factory=lambda: f"vc_{uuid.uuid4().hex[:8]}")
    transcript_id: str
    text: str
    interaction_intent: InteractionIntentType
    confidence: ConfidenceLevel
    target_task_id: Optional[str] = None
    target_step_id: Optional[str] = None
