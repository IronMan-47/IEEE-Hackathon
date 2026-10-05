"""
JARVIS Python Agent Core — Phase 14 Grounded Context Provenance Tags
Defines explicit provenance source tags for context fusion, distinguishing authoritative
system APIs, application adapters, vision models, OCR, and model inferences.
"""

from enum import Enum


class ProvenanceTag(str, Enum):
    WINDOWS_API = "WINDOWS_API"
    APPLICATION_ADAPTER = "APPLICATION_ADAPTER"
    VS_CODE_ADAPTER = "VS_CODE_ADAPTER"
    BROWSER_ADAPTER = "BROWSER_ADAPTER"
    VISION_MODEL = "VISION_MODEL"
    OCR = "OCR"
    MODEL_INFERENCE = "MODEL_INFERENCE"
    USER_EXPLICIT = "USER_EXPLICIT"
    DERIVED = "DERIVED"


SOURCE_PRECEDENCE_SCORES = {
    ProvenanceTag.WINDOWS_API: 100,
    ProvenanceTag.VS_CODE_ADAPTER: 90,
    ProvenanceTag.BROWSER_ADAPTER: 90,
    ProvenanceTag.APPLICATION_ADAPTER: 90,
    ProvenanceTag.USER_EXPLICIT: 85,
    ProvenanceTag.OCR: 75,
    ProvenanceTag.VISION_MODEL: 70,
    ProvenanceTag.DERIVED: 50,
    ProvenanceTag.MODEL_INFERENCE: 40
}


def get_provenance_precedence(tag: ProvenanceTag) -> int:
    return SOURCE_PRECEDENCE_SCORES.get(tag, 10)
