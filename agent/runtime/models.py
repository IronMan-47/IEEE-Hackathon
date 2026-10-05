from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field

class RuntimeStatus(str, Enum):
    STARTING = "STARTING"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING_FOR_HUMAN = "WAITING_FOR_HUMAN"
    PAUSED = "PAUSED"
    RECOVERING = "RECOVERING"
    SAFE_STOPPED = "SAFE_STOPPED"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    SHUTTING_DOWN = "SHUTTING_DOWN"
    STOPPED = "STOPPED"

class RecoveryState(str, Enum):
    NONE = "NONE"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    EXECUTION_UNCERTAIN = "EXECUTION_UNCERTAIN"
    AUTHORIZATION_INVALIDATED = "AUTHORIZATION_INVALIDATED"
    CONTEXT_REVALIDATION_REQUIRED = "CONTEXT_REVALIDATION_REQUIRED"
    HUMAN_DECISION_REQUIRED = "HUMAN_DECISION_REQUIRED"

class AgentRuntimeState(BaseModel):
    runtime_id: str = Field(default_factory=lambda: f"rt_{uuid.uuid4().hex[:8]}")
    runtime_version: str = "17.0.0"
    status: RuntimeStatus = RuntimeStatus.STARTING
    recovery_state: RecoveryState = RecoveryState.NONE
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    python_process_id: Optional[int] = None
    electron_connection_status: str = "DISCONNECTED"
    emergency_stop_state: bool = False
    active_task_id: Optional[str] = None
    active_context_id: Optional[str] = None
    active_execution_id: Optional[str] = None
    last_event_id: Optional[str] = None
    last_event_timestamp: Optional[str] = None
    recovery_required: bool = False

class AgentEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:8]}")
    event_type: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    runtime_id: str
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    task_id: Optional[str] = None
    step_id: Optional[str] = None
    proposal_id: Optional[str] = None
    execution_id: Optional[str] = None
    context_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    schema_version: str = "1.0"
    sequence: int = 0

class RuntimeSnapshot(BaseModel):
    snapshot_id: str = Field(default_factory=lambda: f"snap_{uuid.uuid4().hex[:8]}")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    runtime_state: AgentRuntimeState
    # Minimal necessary references for recovery
    active_task: Optional[Dict[str, Any]] = None
    approval_status: Optional[Dict[str, Any]] = None
    execution_status: Optional[Dict[str, Any]] = None
    last_event_sequence: int = 0
