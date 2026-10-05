import time
from typing import Dict, Any, Optional
from agent.perception.types import AppClassification, PerceptionResult
from agent.adapters.base import BaseAdapter, ApplicationContext, PrivacyLevel, ContextStatus, ContextConfidence

class LivingCanvasAdapter(BaseAdapter):
    adapter_id = "living_canvas"
    supported_classifications = [AppClassification.CODE_EDITOR, AppClassification.DESIGN_TOOL, AppClassification.UNKNOWN]

    def can_handle(self, perception: PerceptionResult) -> bool:
        title = (perception.active_window.title or "").lower()
        proc = (perception.active_application.process_name or "").lower()
        return "living canvas" in title or proc == "electron.exe"

    def get_context(self, perception: PerceptionResult, workspace_context: Optional[Dict[str, Any]] = None) -> ApplicationContext:
        raw_ws = workspace_context or {}

        data = {
            "workspace_id": raw_ws.get("workspaceId", "checkout_demo"),
            "revision": raw_ws.get("revision", 1),
            "element_count": len(raw_ws.get("elements", {})),
            "elements_summary": [
                {
                    "id": el_id,
                    "type": el.get("type"),
                    "label": el.get("label", ""),
                    "w": el.get("w"),
                    "h": el.get("h")
                }
                for el_id, el in raw_ws.get("elements", {}).items()
            ],
            "dirty_state": raw_ws.get("dirty_state", False),
            "reference_environment": True
        }

        return ApplicationContext(
            adapter_id=self.adapter_id,
            application="living_canvas",
            classification=perception.classification,
            timestamp=int(time.time() * 1000),
            status=ContextStatus.AVAILABLE,
            confidence=ContextConfidence.HIGH_CONFIDENCE,
            privacy=PrivacyLevel.PUBLIC,
            capabilities=["workspace", "revision", "elements", "patch_operations", "version_graph"],
            data=data
        )
