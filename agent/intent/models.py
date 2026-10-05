"""
JARVIS Python Agent Core — Phase 8 Intent, Goal, Constraint, & Planning Models
"""

import uuid
import re
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class IntentCategory(str, Enum):
    EXPLAIN = "EXPLAIN"
    ANALYZE = "ANALYZE"
    CREATE = "CREATE"
    EDIT = "EDIT"
    REFACTOR = "REFACTOR"
    DEBUG = "DEBUG"
    DESIGN = "DESIGN"
    SEARCH = "SEARCH"
    COMPARE = "COMPARE"
    SUMMARIZE = "SUMMARIZE"
    NAVIGATE = "NAVIGATE"
    PLAN = "PLAN"
    UNKNOWN = "UNKNOWN"
    PROPOSE_CHANGE = "PROPOSE_CHANGE"
    EXPLAIN_WORKSPACE = "EXPLAIN_WORKSPACE"
    UNSUPPORTED_REQUEST = "UNSUPPORTED_REQUEST"


class IntentConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class TargetType(str, Enum):
    ACTIVE_APPLICATION = "ACTIVE_APPLICATION"
    ACTIVE_FILE = "ACTIVE_FILE"
    ACTIVE_DOCUMENT = "ACTIVE_DOCUMENT"
    ACTIVE_PAGE = "ACTIVE_PAGE"
    ACTIVE_CANVAS = "ACTIVE_CANVAS"
    CURRENT_WORKSPACE = "CURRENT_WORKSPACE"
    SELECTED_ELEMENT = "SELECTED_ELEMENT"
    UNKNOWN = "UNKNOWN"


class TargetResolution(BaseModel):
    type: TargetType = TargetType.UNKNOWN
    name: Optional[str] = None


class ConstraintType(str, Enum):
    PRESERVE_BEHAVIOR = "PRESERVE_BEHAVIOR"
    MINIMAL_CHANGE = "MINIMAL_CHANGE"
    DO_NOT_DELETE = "DO_NOT_DELETE"
    DO_NOT_RENAME = "DO_NOT_RENAME"
    KEEP_API_COMPATIBILITY = "KEEP_API_COMPATIBILITY"
    PRESERVE_DESIGN = "PRESERVE_DESIGN"
    USE_EXISTING_STYLE = "USE_EXISTING_STYLE"
    LIMIT_SCOPE = "LIMIT_SCOPE"


class ConstraintSource(str, Enum):
    EXPLICIT = "EXPLICIT"
    INFERRED = "INFERRED"
    SYSTEM_SAFETY = "SYSTEM_SAFETY"


class Constraint(BaseModel):
    type: ConstraintType
    source: ConstraintSource
    description: Optional[str] = None


class UserRequest(BaseModel):
    id: str = Field(default_factory=lambda: f"req_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:6]}")
    text: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = "USER"
    language: str = "en"
    explicit_constraints: List[str] = Field(default_factory=list)


class RequestNormalizer:
    MAX_LENGTH: int = 2000

    @classmethod
    def normalize(cls, raw_text: str, request_id: Optional[str] = None) -> UserRequest:
        if not raw_text or not isinstance(raw_text, str):
            raise ValueError("User request must be a non-empty string.")
        
        trimmed = raw_text.strip()
        if not trimmed:
            raise ValueError("User request cannot be empty or whitespace only.")
        
        if len(trimmed) > cls.MAX_LENGTH:
            trimmed = trimmed[:cls.MAX_LENGTH]
        
        normalized_text = re.sub(r'\s+', ' ', trimmed)
        
        req_id = request_id or f"req_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:6]}"
        return UserRequest(
            id=req_id,
            text=normalized_text,
            timestamp=datetime.now(timezone.utc).isoformat()
        )


class Intent(BaseModel):
    intent_type: IntentCategory
    confidence: IntentConfidence = IntentConfidence.MEDIUM
    target: TargetResolution = Field(default_factory=TargetResolution)
    reason: str = "Classified based on request text and context"


class Goal(BaseModel):
    primary_goal: str
    success_condition: str
    target: TargetType = TargetType.UNKNOWN


class ClarificationRequest(BaseModel):
    needs_clarification: bool = True
    question: str
    reason: str
    missing_information: List[str] = Field(default_factory=list)


class PlanStepType(str, Enum):
    OBSERVE = "OBSERVE"
    ANALYZE = "ANALYZE"
    REASON = "REASON"
    PROPOSE = "PROPOSE"
    VERIFY = "VERIFY"
    ASK_USER = "ASK_USER"


class PlanStep(BaseModel):
    id: str
    type: PlanStepType
    description: str
    target_id: Optional[str] = None
    reason: Optional[str] = None


class PlanAuthor(str, Enum):
    AI = "AI"
    HUMAN_MODIFIED = "HUMAN_MODIFIED"


class PlanStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    STALE = "STALE"


class Plan(BaseModel):
    plan_id: str = Field(default_factory=lambda: f"plan_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:6]}")
    request_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    context_snapshot_id: str
    context_hash: str
    intent: IntentCategory
    goal: Goal
    constraints: List[Constraint] = Field(default_factory=list)
    steps: List[PlanStep] = Field(default_factory=list)
    reasoning_summary: str
    version: int = 1
    author: PlanAuthor = PlanAuthor.AI
    parent_plan_id: Optional[str] = None
    status: PlanStatus = PlanStatus.DRAFT

    def is_stale(self, current_context_hash: str) -> bool:
        return self.context_hash != current_context_hash
