"""
JARVIS Python Agent Core — Phase 14 Grounded Context Models
Defines typed GroundedContext, FactStatement, ApplicationRole, and AppInfo models.
"""

import time
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from agent.perception.visual.models import VisualContext, VisualElement, VisualRegion
from agent.context.fusion.provenance import ProvenanceTag
from agent.context.fusion.evidence import Evidence
from agent.context.fusion.conflicts import ContextConflict


class FactType(str, Enum):
    FACT = "FACT"
    OBSERVED = "OBSERVED"
    INFERENCE = "INFERENCE"
    UNKNOWN = "UNKNOWN"


class FactStatement(BaseModel):
    id: str
    statement: str
    type: FactType = Field(default=FactType.FACT)
    provenance: ProvenanceTag = Field(default=ProvenanceTag.WINDOWS_API)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    model_config = ConfigDict(frozen=False)


class ApplicationRole(str, Enum):
    PRIMARY_APPLICATION = "PRIMARY_APPLICATION"
    SECONDARY_APPLICATION = "SECONDARY_APPLICATION"


class AppInfo(BaseModel):
    name: str = Field(default="Unknown Application")
    process_name: str = Field(default="unknown.exe")
    role: ApplicationRole = Field(default=ApplicationRole.PRIMARY_APPLICATION)
    details: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=False)


class GroundedContext(BaseModel):
    context_id: str
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))
    request_id: Optional[str] = Field(default=None)
    primary_application: AppInfo = Field(default_factory=AppInfo)
    secondary_applications: List[AppInfo] = Field(default_factory=list)
    application_context: Dict[str, Any] = Field(default_factory=dict)
    visual_context: Optional[VisualContext] = Field(default=None)
    relevant_regions: List[VisualRegion] = Field(default_factory=list)
    relevant_elements: List[VisualElement] = Field(default_factory=list)
    user_request: Optional[str] = Field(default=None)
    active_target: Optional[Any] = Field(default=None) # TargetReference
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    conflicts: List[ContextConflict] = Field(default_factory=list)
    evidence_list: List[Evidence] = Field(default_factory=list)
    facts: List[FactStatement] = Field(default_factory=list)
    provenance: ProvenanceTag = Field(default=ProvenanceTag.WINDOWS_API)
    context_hash: str = Field(default="")
    is_stale: bool = Field(default=False)
    stale_reason: Optional[str] = Field(default=None)
    clarification_required: bool = Field(default=False)
    clarification_question: Optional[str] = Field(default=None)

    model_config = ConfigDict(frozen=False)
