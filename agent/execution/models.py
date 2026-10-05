"""
JARVIS Python Agent Core — Phase 10 Controlled Execution Engine Models
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    COMMITTED = "COMMITTED"
    FAILED = "FAILED"
    REVERTED = "REVERTED"
    BLOCKED = "BLOCKED"


class ExecutionRequest(BaseModel):
    execution_id: str = Field(default_factory=lambda: f"exec_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:6]}")
    proposal_id: str
    approval_token: Dict[str, Any]
    workspace_id: str = "checkout_demo"
    base_revision: int
    base_context_id: str
    base_context_hash: str
    requested_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    requested_by: str = "HUMAN"


class ExecutionResult(BaseModel):
    status: ExecutionStatus
    execution_id: str
    proposal_id: str
    workspace_id: str
    previous_revision: int
    new_revision: int
    verification: str  # "PASSED" | "FAILED" | "SKIPPED"
    version_id: Optional[str] = None
    error: Optional[str] = None
    operations_applied: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
