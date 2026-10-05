import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from enum import Enum
import re
from agent.core.logging import logger

class WorkflowContextLinkType(str, Enum):
    SOURCE_OF = "SOURCE_OF"
    DERIVED_FROM = "DERIVED_FROM"
    REFERENCES = "REFERENCES"
    VALIDATES = "VALIDATES"
    CONTRADICTS = "CONTRADICTS"
    TARGET_FOR = "TARGET_FOR"
    RETURN_CONTEXT = "RETURN_CONTEXT"
    RESEARCH_SOURCE = "RESEARCH_SOURCE"
    PROPOSED_FIX_SOURCE = "PROPOSED_FIX_SOURCE"

class WorkflowContextLink(BaseModel):
    link_id: str = Field(default_factory=lambda: f"link_{uuid.uuid4().hex[:6]}")
    source_context_id: str
    target_context_id: str
    relationship: WorkflowContextLinkType
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    confidence: float = 1.0
    provenance: str = "CONTEXT_RESOLVER"

class HandoffStatus(str, Enum):
    PENDING = "PENDING"
    SANITIZED = "SANITIZED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    STALE = "STALE"
    BLOCKED = "BLOCKED"

class CrossApplicationContext(BaseModel):
    workflow_id: str
    source_application: str
    source_context_id: str
    source_context_hash: str
    source_revision: str
    target_application: str
    target_context_id: Optional[str] = None
    target_context_hash: Optional[str] = None
    target_revision: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    evidence_links: List[WorkflowContextLink] = Field(default_factory=list)
    handoff_status: HandoffStatus = HandoffStatus.PENDING
    confidence: float = 1.0
    sanitized_payload: Dict[str, Any] = Field(default_factory=dict)
    provenance: str = "CROSS_APP_HANDOFF"
    staleness_state: bool = False

class ContextSanitizer:
    # Basic regex patterns for secrets and sensitive data
    SECRET_PATTERNS = [
        (re.compile(r'password\s*[:=]\s*["\']([^"\']+)["\']', re.IGNORECASE), "REDACTED_PASSWORD"),
        (re.compile(r'bearer\s+([a-zA-Z0-9_\-\.]+)', re.IGNORECASE), "REDACTED_BEARER_TOKEN"),
        (re.compile(r'api_?key\s*[:=]\s*["\']([^"\']+)["\']', re.IGNORECASE), "REDACTED_API_KEY"),
        (re.compile(r'(?:\d{4}[-\s]?){3}\d{4}'), "REDACTED_CARD_NUMBER"), # simple CC format
        (re.compile(r'\b(?:secret|token)\s*[:=]\s*["\']([^"\']+)["\']', re.IGNORECASE), "REDACTED_SECRET")
    ]

    @classmethod
    def sanitize(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively sanitizes dictionaries and strings to remove sensitive cross-application data.
        """
        sanitized = {}
        for k, v in data.items():
            if isinstance(v, str):
                sanitized[k] = cls._sanitize_string(v)
            elif isinstance(v, dict):
                sanitized[k] = cls.sanitize(v)
            elif isinstance(v, list):
                sanitized[k] = [
                    cls._sanitize_string(i) if isinstance(i, str) else (cls.sanitize(i) if isinstance(i, dict) else i)
                    for i in v
                ]
            else:
                sanitized[k] = v
        return sanitized

    @classmethod
    def _sanitize_string(cls, text: str) -> str:
        sanitized_text = text
        for pattern, replacement in cls.SECRET_PATTERNS:
            sanitized_text = pattern.sub(replacement, sanitized_text)
        return sanitized_text

class CrossAppHandoffManager:
    """
    Manages the creation, sanitization, and verification of context handoffs.
    """
    @classmethod
    def create_handoff(
        cls, 
        workflow_id: str, 
        source_app: str, 
        target_app: str, 
        source_context, 
        relevant_evidence: Dict[str, Any]
    ) -> CrossApplicationContext:
        
        sanitized_evidence = ContextSanitizer.sanitize(relevant_evidence)
        
        handoff = CrossApplicationContext(
            workflow_id=workflow_id,
            source_application=source_app,
            source_context_id=source_context.context_id,
            source_context_hash=source_context.context_hash,
            source_revision=str(getattr(source_context, 'timestamp', '0')),
            target_application=target_app,
            sanitized_payload=sanitized_evidence,
            handoff_status=HandoffStatus.SANITIZED
        )
        
        logger.info(f"AUDIT EVENT [CONTEXT_HANDOFF_CREATED] Workflow [{workflow_id}]: {source_app} -> {target_app}")
        
        # Emit event if runtime is initialized
        try:
            from agent.runtime.lifecycle import runtime_manager
            runtime_manager._emit("CONTEXT_HANDOFF_CREATED", handoff.model_dump())
        except ImportError:
            pass
            
        return handoff

    @classmethod
    def verify_target_context(cls, handoff: CrossApplicationContext, target_context) -> bool:
        """
        Verifies that the target application matches the expected application for the handoff.
        """
        current_app = target_context.primary_application.name.lower()
        expected_app = handoff.target_application.lower()
        
        # Simple string inclusion check (e.g., "visual studio code" vs "vscode")
        if expected_app not in current_app and current_app not in expected_app:
            if not ((expected_app == "browser" and ("chrome" in current_app or "edge" in current_app)) or
                    (expected_app == "vscode" and "visual studio code" in current_app)):
                logger.warning(f"AUDIT EVENT [APPLICATION_TRANSITION_BLOCKED]: Expected {expected_app}, found {current_app}")
                handoff.handoff_status = HandoffStatus.BLOCKED
                return False
                
        handoff.target_context_id = target_context.context_id
        handoff.target_context_hash = target_context.context_hash
        handoff.target_revision = str(getattr(target_context, 'timestamp', '0'))
        handoff.handoff_status = HandoffStatus.ACCEPTED
        
        logger.info(f"AUDIT EVENT [TARGET_APPLICATION_VERIFIED] Target context {target_context.context_id} accepted.")
        return True
