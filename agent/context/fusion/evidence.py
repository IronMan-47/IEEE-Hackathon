"""
JARVIS Python Agent Core — Phase 14 Evidence Model
Defines typed evidence records linking grounded facts to specific perception sources.
"""

import time
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from agent.context.fusion.provenance import ProvenanceTag


class EvidenceType(str, Enum):
    WINDOW_METADATA = "WINDOW_METADATA"
    APPLICATION_CONTEXT = "APPLICATION_CONTEXT"
    VISUAL_ELEMENT = "VISUAL_ELEMENT"
    OCR_TEXT = "OCR_TEXT"
    USER_REQUEST = "USER_REQUEST"
    WORKSPACE_STATE = "WORKSPACE_STATE"
    BROWSER_CONTEXT = "BROWSER_CONTEXT"
    CODE_CONTEXT = "CODE_CONTEXT"


class Evidence(BaseModel):
    evidence_id: str
    type: EvidenceType
    source: ProvenanceTag
    content_reference: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))
    relevance: float = Field(default=1.0, ge=0.0, le=1.0)
    details: Optional[Dict[str, Any]] = Field(default=None)

    model_config = ConfigDict(frozen=False)
