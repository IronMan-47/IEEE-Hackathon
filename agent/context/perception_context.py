from enum import Enum
from typing import Dict, Any, Optional
from agent.perception.types import PerceptionResult

class ContextSource(str, Enum):
    LIVING_CANVAS = "LIVING_CANVAS"
    DESKTOP_PERCEPTION = "DESKTOP_PERCEPTION"

class ContextBuilder:
    @staticmethod
    def build_desktop_context(perception: PerceptionResult) -> Dict[str, Any]:
        return {
            "source": ContextSource.DESKTOP_PERCEPTION.value,
            "timestamp": perception.timestamp,
            "perception_enabled": perception.perception_enabled,
            "is_excluded": perception.is_excluded,
            "active_application": perception.active_application.model_dump(),
            "active_window": perception.active_window.model_dump(),
            "screen": perception.screen_metadata.model_dump(),
            "classification": perception.classification.value,
            "capture_available": perception.capture_metadata.captured
        }

    @staticmethod
    def build_combined_context(
        workspace_context: Optional[Dict[str, Any]] = None,
        perception_context: Optional[PerceptionResult] = None
    ) -> Dict[str, Any]:
        result = {}

        if perception_context:
            result["desktop"] = ContextBuilder.build_desktop_context(perception_context)

        if workspace_context:
            result["living_canvas"] = workspace_context

        if "desktop" in result:
            result["primary_source"] = ContextSource.DESKTOP_PERCEPTION.value
        else:
            result["primary_source"] = ContextSource.LIVING_CANVAS.value

        return result
