"""
JARVIS Python Agent Core — Workspace Context Model
"""

from typing import Dict, Any, List

class WorkspaceContextModel:
    def __init__(self, raw_context: Dict[str, Any]):
        self.raw = raw_context
        self.revision: int = raw_context.get("revision", 1)
        self.title: str = raw_context.get("title", "Living Canvas Workspace")
        self.elements: Dict[str, Any] = raw_context.get("elements", {})

    def get_element_summary(self) -> List[Dict[str, Any]]:
        summary = []
        for el_id, el in self.elements.items():
            summary.append({
                "id": el_id,
                "type": el.get("type"),
                "label": el.get("label", ""),
                "x": el.get("x"),
                "y": el.get("y"),
                "w": el.get("w"),
                "h": el.get("h"),
                "style": el.get("style", {})
            })
        return summary
