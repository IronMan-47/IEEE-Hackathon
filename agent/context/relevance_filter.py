"""
JARVIS Python Agent Core — Phase 8 Context Relevance Filter
Filters perception metadata into RelevantContext and isolates untrusted data boundaries.
"""

import hashlib
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class RelevantContext(BaseModel):
    context_id: str
    context_hash: str
    active_app_domain: str = "unknown"
    active_app_name: str = "Unknown"
    active_window_title: str = "Unknown Window"
    active_file: Optional[str] = None
    language: Optional[str] = None
    workspace_name: Optional[str] = None
    workspace_revision: int = 0
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
    raw_title: str = ""
    _untrusted_data_boundary: bool = True

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["_untrusted_data_boundary"] = True
        return d


class ContextRelevanceFilter:
    @classmethod
    def filter(cls, perception_dict: Optional[Dict[str, Any]], workspace_dict: Optional[Dict[str, Any]]) -> RelevantContext:
        perception = perception_dict or {}
        workspace = workspace_dict or {}

        app_context = perception.get("application_context", {})
        active_window = perception.get("active_window", {})
        active_app = perception.get("active_application", {})

        domain = app_context.get("domain", "unknown")
        extracted = app_context.get("extracted_fields", {})
        raw_title = app_context.get("raw_title") or active_window.get("title", "") or active_app.get("name", "Unknown")

        active_file = extracted.get("active_file") or extracted.get("active_page") or extracted.get("workspace_name")
        language = extracted.get("language")
        ws_name = extracted.get("workspace_name")
        ws_rev = workspace.get("revision", 0)

        # Build clean dict representation omitting irrelevant bounds, DPI, PID
        filtered_dict = {
            "domain": domain,
            "app_name": active_app.get("name", "Unknown"),
            "raw_title": raw_title,
            "extracted_fields": extracted,
            "workspace_revision": ws_rev
        }

        # Calculate context hash
        json_str = json.dumps(filtered_dict, sort_keys=True)
        context_hash = hashlib.sha256(json_str.encode("utf-8")).hexdigest()[:16]
        context_id = f"ctx_{context_hash[:8]}"

        return RelevantContext(
            context_id=context_id,
            context_hash=context_hash,
            active_app_domain=domain,
            active_app_name=active_app.get("name", "Unknown"),
            active_window_title=raw_title,
            active_file=active_file,
            language=language,
            workspace_name=ws_name,
            workspace_revision=ws_rev,
            extracted_fields=extracted,
            raw_title=raw_title,
            _untrusted_data_boundary=True
        )
