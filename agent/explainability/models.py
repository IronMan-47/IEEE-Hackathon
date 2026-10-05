from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class EpistemicStatus(str, Enum):
    FACT = "FACT"
    OBSERVED = "OBSERVED"
    INFERENCE = "INFERENCE"
    UNKNOWN = "UNKNOWN"

class ExplanationDepth(str, Enum):
    COMPACT = "COMPACT"
    STANDARD = "STANDARD"
    DETAILED = "DETAILED"

class RiskExplanation(BaseModel):
    level: str = Field(description="HIGH, MEDIUM, LOW")
    reason: str
    mitigation: Optional[str] = None

class Explanation(BaseModel):
    explanation_id: str
    subject_type: str = Field(description="What is being explained, e.g., 'STEP', 'TASK_PAUSE', 'VALIDATION'")
    summary: str
    reason: str
    evidence_ids: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    risk: Optional[RiskExplanation] = None
    expected_outcome: Optional[str] = None
    epistemic_status: EpistemicStatus = Field(default=EpistemicStatus.INFERENCE)

class InteractionIntent(BaseModel):
    intent_type: str = Field(description="e.g., 'MODIFY_STEP', 'CLARIFY_TARGET', 'REJECT_PROPOSAL'")
    target_id: Optional[str] = None
    modification_instructions: Optional[str] = None

class TaskModification(BaseModel):
    modification_id: str
    original_step_id: str
    new_step_id: str
    reason: str
    interaction_intent_id: Optional[str] = None
