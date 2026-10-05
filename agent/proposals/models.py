"""
JARVIS Python Agent Core — Phase 9 Proposal Models & Domain Vocabulary
"""

import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from agent.intent.models import Constraint, Goal, IntentCategory


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    DESTRUCTIVE = "DESTRUCTIVE"


class ProposalStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    MODIFIED = "MODIFIED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    STALE = "STALE"
    INVALID = "INVALID"
    CONFLICT = "CONFLICT"


class ProposalOperation(BaseModel):
    operation_id: str = Field(default_factory=lambda: f"op_{uuid.uuid4().hex[:6]}")
    op_type: str
    target: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    reason: str
    risk: RiskLevel = RiskLevel.LOW


class Proposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: f"prop_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:6]}")
    request_id: str
    plan_id: str
    domain: str = "living_canvas"  # "living_canvas" | "vscode" | "browser" | "terminal" | "figma" | "unknown"
    base_context_id: str
    base_context_hash: str
    base_revision: int = 0
    title: str
    summary: str
    reason: str
    operations: List[ProposalOperation] = Field(default_factory=list)
    constraints: List[Constraint] = Field(default_factory=list)
    risk: RiskLevel = RiskLevel.LOW
    status: ProposalStatus = ProposalStatus.DRAFT
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: str = Field(default_factory=lambda: (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat())
    source: str = "AI"  # "AI" | "HUMAN_MODIFIED"
    parent_proposal_id: Optional[str] = None
    version: int = 1
    trace: Dict[str, Any] = Field(default_factory=dict)

    def is_expired(self) -> bool:
        try:
            exp = datetime.fromisoformat(self.expires_at)
            return datetime.now(timezone.utc) > exp
        except Exception:
            return False

    def is_stale(self, current_context_hash: str) -> bool:
        return self.base_context_hash != current_context_hash
