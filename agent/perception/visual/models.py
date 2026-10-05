"""
JARVIS Python Agent Core — Phase 13 Visual Context & Element Models
Defines typed models for visual screen perception, bounding boxes, visual elements,
visual regions, confidence levels, provenance tracking, and visual contexts.
"""

import time
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class ConfidenceLevel(str, Enum):
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
    MEDIUM_CONFIDENCE = "MEDIUM_CONFIDENCE"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"


def get_confidence_level(score: float) -> ConfidenceLevel:
    if score >= 0.8:
        return ConfidenceLevel.HIGH_CONFIDENCE
    elif score >= 0.5:
        return ConfidenceLevel.MEDIUM_CONFIDENCE
    return ConfidenceLevel.LOW_CONFIDENCE


class ProvenanceSource(str, Enum):
    SCREENSHOT = "SCREENSHOT"
    WINDOW_METADATA = "WINDOW_METADATA"
    APPLICATION_ADAPTER = "APPLICATION_ADAPTER"
    OCR = "OCR"
    VISION_MODEL = "VISION_MODEL"
    DERIVED = "DERIVED"


class VisualElementType(str, Enum):
    BUTTON = "BUTTON"
    TEXT = "TEXT"
    HEADING = "HEADING"
    INPUT = "INPUT"
    CHECKBOX = "CHECKBOX"
    RADIO = "RADIO"
    DROPDOWN = "DROPDOWN"
    TAB = "TAB"
    MENU = "MENU"
    TOOLBAR = "TOOLBAR"
    CARD = "CARD"
    IMAGE = "IMAGE"
    ICON = "ICON"
    TABLE = "TABLE"
    LIST = "LIST"
    CODE_REGION = "CODE_REGION"
    PANEL = "PANEL"
    DIALOG = "DIALOG"
    NAVIGATION = "NAVIGATION"
    UNKNOWN = "UNKNOWN"


class BoundingBox(BaseModel):
    x: int = Field(default=0, ge=0)
    y: int = Field(default=0, ge=0)
    width: int = Field(default=0, ge=0)
    height: int = Field(default=0, ge=0)

    model_config = ConfigDict(frozen=False)


class VisualElement(BaseModel):
    id: str
    type: VisualElementType = Field(default=VisualElementType.UNKNOWN)
    role: Optional[str] = Field(default=None)
    bounds: BoundingBox = Field(default_factory=BoundingBox)
    text: Optional[str] = Field(default=None)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel = Field(default=ConfidenceLevel.HIGH_CONFIDENCE)
    parent_id: Optional[str] = Field(default=None)
    state: Optional[Dict[str, Any]] = Field(default=None)
    provenance: ProvenanceSource = Field(default=ProvenanceSource.VISION_MODEL)

    model_config = ConfigDict(frozen=False)


class VisualRegion(BaseModel):
    id: str
    name: str
    bounds: BoundingBox = Field(default_factory=BoundingBox)
    element_ids: List[str] = Field(default_factory=list)
    parent_id: Optional[str] = Field(default=None)
    provenance: ProvenanceSource = Field(default=ProvenanceSource.VISION_MODEL)

    model_config = ConfigDict(frozen=False)


class VisualContext(BaseModel):
    context_id: str
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))
    screen_id: int = Field(default=0)
    monitor_id: int = Field(default=0)
    bounds: BoundingBox = Field(default_factory=BoundingBox)
    application: str = Field(default="Unknown")
    application_class: str = Field(default="UNKNOWN")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel = Field(default=ConfidenceLevel.HIGH_CONFIDENCE)
    regions: List[VisualRegion] = Field(default_factory=list)
    elements: List[VisualElement] = Field(default_factory=list)
    visual_summary: str = Field(default="")
    context_hash: str = Field(default="")
    provenance: ProvenanceSource = Field(default=ProvenanceSource.VISION_MODEL)
    is_sensitive: bool = Field(default=False)
    redacted_elements_count: int = Field(default=0)

    model_config = ConfigDict(frozen=False)
