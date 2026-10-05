"""
JARVIS Python Agent Core — Phase 14 Context Conflict Detection & Resolution Model
Defines conflict models for detecting mismatches between perception sources (e.g., Windows API vs Vision Model)
and resolving them deterministically using source precedence or triggering clarification requests.
"""

import time
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from agent.context.fusion.provenance import ProvenanceTag


class ConflictType(str, Enum):
    APPLICATION_MISMATCH = "APPLICATION_MISMATCH"
    WINDOW_MISMATCH = "WINDOW_MISMATCH"
    FILE_MISMATCH = "FILE_MISMATCH"
    ORIGIN_MISMATCH = "ORIGIN_MISMATCH"
    TARGET_MISMATCH = "TARGET_MISMATCH"
    VISUAL_METADATA_MISMATCH = "VISUAL_METADATA_MISMATCH"
    STALE_CONTEXT = "STALE_CONTEXT"
    IDENTITY_UNCERTAIN = "IDENTITY_UNCERTAIN"


class ConflictResolution(str, Enum):
    AUTHORITATIVE_SOURCE = "AUTHORITATIVE_SOURCE"
    USER_CLARIFICATION_REQUIRED = "USER_CLARIFICATION_REQUIRED"
    STALE = "STALE"
    UNRESOLVED = "UNRESOLVED"


class ContextConflict(BaseModel):
    conflict_id: str
    type: ConflictType
    sources: List[ProvenanceTag]
    fields: List[str]
    values: Dict[str, Any]
    severity: str = Field(default="HIGH") # HIGH, MEDIUM, LOW
    detected_at: int = Field(default_factory=lambda: int(time.time() * 1000))
    resolution: ConflictResolution = Field(default=ConflictResolution.UNRESOLVED)
    resolution_source: Optional[ProvenanceTag] = Field(default=None)
    details: Optional[str] = Field(default=None)

    model_config = ConfigDict(frozen=False)
