import time
from agent.perception.types import AppClassification, PerceptionResult
from agent.adapters.base import BaseAdapter, ApplicationContext, PrivacyLevel, ContextStatus, ContextConfidence

class UnknownAdapter(BaseAdapter):
    adapter_id = "unknown"
    supported_classifications = [
        AppClassification.CODE_EDITOR,
        AppClassification.BROWSER,
        AppClassification.DESIGN_TOOL,
        AppClassification.TERMINAL,
        AppClassification.DOCUMENT_EDITOR,
        AppClassification.UNKNOWN
    ]

    def can_handle(self, perception: PerceptionResult) -> bool:
        return True # Fallback matching for any application without a specialized adapter

    def get_context(self, perception: PerceptionResult) -> ApplicationContext:
        proc_name = perception.active_application.process_name or "unknown.exe"
        win_title = perception.active_window.title or "Unknown Window"

        data = {
            "application_process": proc_name,
            "window_title": win_title,
            "context_status": "UNSUPPORTED",
            "reason": f"No specialized domain adapter registered for process [{proc_name}]"
        }

        return ApplicationContext(
            adapter_id=self.adapter_id,
            application="unknown",
            classification=perception.classification,
            timestamp=int(time.time() * 1000),
            status=ContextStatus.UNSUPPORTED,
            confidence=ContextConfidence.UNAVAILABLE,
            privacy=PrivacyLevel.PUBLIC,
            capabilities=[],
            data=data
        )
