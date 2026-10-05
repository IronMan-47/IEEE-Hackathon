"""
JARVIS Python Agent Core — Phase 15 Task Orchestration Models
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from agent.proposals.models import Proposal
from agent.execution.models import ExecutionResult
from agent.context.fusion.models import GroundedContext
from agent.explainability.models import Explanation


class TaskStatus(str, Enum):
    CREATED = "CREATED"
    UNDERSTANDING = "UNDERSTANDING"
    PLANNING = "PLANNING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    REASSESSING = "REASSESSING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ApprovalPolicy(str, Enum):
    STEP_BY_STEP = "STEP_BY_STEP"  # Mandatory: Every executable step requires explicit human review and ApprovalToken


class TaskStepType(str, Enum):
    OBSERVE = "OBSERVE"
    ANALYZE = "ANALYZE"
    REASON = "REASON"
    PROPOSE = "PROPOSE"
    WAIT_FOR_APPROVAL = "WAIT_FOR_APPROVAL"
    EXECUTE = "EXECUTE"
    VERIFY = "VERIFY"
    REASSESS = "REASSESS"
    REPORT = "REPORT"
    ASK_USER = "ASK_USER"


class TaskStepStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"


class TaskBudget(BaseModel):
    max_steps: int = 10
    max_replans: int = 3
    current_steps: int = 0
    current_replans: int = 0


class TaskStep(BaseModel):
    step_id: str = Field(default_factory=lambda: f"step_{uuid.uuid4().hex[:6]}")
    step_number: int
    step_type: TaskStepType
    title: str
    description: str
    depends_on: List[str] = Field(default_factory=list)
    target_domain: Optional[str] = None  # "living_canvas", "vscode", "browser", "unsupported_domain"
    expected_postcondition: Optional[str] = None
    proposal: Optional[Proposal] = None
    approval_token: Optional[Dict[str, Any]] = None
    execution_result: Optional[ExecutionResult] = None
    status: TaskStepStatus = TaskStepStatus.PENDING
    verification_status: Optional[str] = None  # "PASSED" | "FAILED" | "SKIPPED" | "PENDING"
    error: Optional[str] = None
    explanation: Optional[Explanation] = None
    cross_app_handoff: Optional[Dict[str, Any]] = None  # Phase 19 cross-app handoff
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None


class Task(BaseModel):
    task_id: str = Field(default_factory=lambda: f"task_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:6]}")
    user_request: str
    normalized_request_id: str
    status: TaskStatus = TaskStatus.CREATED
    approval_policy: ApprovalPolicy = ApprovalPolicy.STEP_BY_STEP
    budget: TaskBudget = Field(default_factory=TaskBudget)
    steps: List[TaskStep] = Field(default_factory=list)
    current_step_index: int = 0
    initial_context_hash: str = ""
    last_context_hash: str = ""
    active_handoff: Optional[Dict[str, Any]] = None # Phase 19 cross app handoff
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    error: Optional[str] = None
    explanation: Optional[Explanation] = None
    grounded_context: Optional[GroundedContext] = None
    verification_history: List[Dict[str, Any]] = Field(default_factory=list)
