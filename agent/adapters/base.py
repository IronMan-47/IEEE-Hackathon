from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from agent.perception.types import AppClassification, PerceptionResult

class PrivacyLevel(str, Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    SENSITIVE = "SENSITIVE"
    RESTRICTED = "RESTRICTED"

class ContextStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    UNSUPPORTED = "UNSUPPORTED"

class ContextConfidence(str, Enum):
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"

class ApplicationContext(BaseModel):
    source: str = Field(default="APPLICATION_ADAPTER")
    adapter_id: str = Field(default="base_adapter")
    application: str = Field(default="unknown")
    classification: AppClassification = Field(default=AppClassification.UNKNOWN)
    timestamp: int = Field(default=0)
    status: ContextStatus = Field(default=ContextStatus.UNSUPPORTED)
    confidence: ContextConfidence = Field(default=ContextConfidence.UNAVAILABLE)
    privacy: PrivacyLevel = Field(default=PrivacyLevel.PUBLIC)
    capabilities: List[str] = Field(default_factory=list)
    data: Dict[str, Any] = Field(default_factory=dict)

class BaseAdapter:
    adapter_id: str = "base"
    supported_classifications: List[AppClassification] = []

    def can_handle(self, perception: PerceptionResult) -> bool:
        return perception.classification in self.supported_classifications

    def get_context(self, perception: PerceptionResult) -> ApplicationContext:
        raise NotImplementedError("Subclasses must implement get_context")
