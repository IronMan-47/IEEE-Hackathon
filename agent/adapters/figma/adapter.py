import time
from typing import Dict, Any, Optional
from agent.perception.types import AppClassification, PerceptionResult
from agent.adapters.base import BaseAdapter, ApplicationContext, PrivacyLevel, ContextStatus, ContextConfidence

class FigmaAdapter(BaseAdapter):
    adapter_id = "figma"
    supported_classifications = [AppClassification.DESIGN_TOOL]

    def can_handle(self, perception: PerceptionResult) -> bool:
        proc = (perception.active_application.process_name or "").lower()
        title = (perception.active_window.title or "").lower()
        return proc == "figma.exe" or "figma" in title

    def get_context(self, perception: PerceptionResult, mock_data: Optional[Dict[str, Any]] = None) -> ApplicationContext:
        if mock_data:
            return ApplicationContext(
                adapter_id=self.adapter_id,
                application="figma",
                classification=AppClassification.DESIGN_TOOL,
                timestamp=int(time.time() * 1000),
                status=ContextStatus.AVAILABLE,
                confidence=ContextConfidence.HIGH_CONFIDENCE,
                privacy=PrivacyLevel.PRIVATE,
                capabilities=["document_name", "selection"],
                data=mock_data
            )

        title = perception.active_window.title or ""
        doc_name = title.replace(" – Figma", "").replace(" - Figma", "").strip()

        data = {
            "file": doc_name or "Figma Document",
            "page": "UNAVAILABLE",
            "selection": "UNAVAILABLE",
            "selected_nodes": [],
            "status_reason": "No safe read-only provider configured for Desktop Figma API"
        }

        return ApplicationContext(
            adapter_id=self.adapter_id,
            application="figma",
            classification=AppClassification.DESIGN_TOOL,
            timestamp=int(time.time() * 1000),
            status=ContextStatus.UNAVAILABLE,
            confidence=ContextConfidence.PARTIAL,
            privacy=PrivacyLevel.PRIVATE,
            capabilities=["document_title"],
            data=data
        )
