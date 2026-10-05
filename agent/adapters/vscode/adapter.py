import os
import time
from typing import Dict, Any, Optional, Tuple
from agent.perception.types import AppClassification, PerceptionResult
from agent.adapters.base import BaseAdapter, ApplicationContext, PrivacyLevel, ContextStatus, ContextConfidence

class VSCodeAdapter(BaseAdapter):
    adapter_id = "vscode"
    supported_classifications = [AppClassification.CODE_EDITOR]

    def can_handle(self, perception: PerceptionResult) -> bool:
        proc = (perception.active_application.process_name or "").lower()
        title = (perception.active_window.title or "").lower()
        return proc in {"code.exe", "code - insiders.exe", "vsc.exe"} or "visual studio code" in title

    def get_context(self, perception: PerceptionResult, mock_data: Optional[Dict[str, Any]] = None) -> ApplicationContext:
        if mock_data:
            return ApplicationContext(
                adapter_id=self.adapter_id,
                application="vscode",
                classification=AppClassification.CODE_EDITOR,
                timestamp=int(time.time() * 1000),
                status=ContextStatus.AVAILABLE,
                confidence=ContextConfidence.HIGH_CONFIDENCE,
                privacy=PrivacyLevel.PRIVATE,
                capabilities=["workspace", "active_file", "language"],
                data=mock_data
            )

        title = perception.active_window.title or ""
        file_name, workspace_name = self._parse_vscode_title(title)

        ext = os.path.splitext(file_name)[1].lower() if file_name else ""
        lang_map = {
            ".py": "python",
            ".ts": "typescript",
            ".js": "javascript",
            ".json": "json",
            ".html": "html",
            ".css": "css",
            ".md": "markdown"
        }
        language = lang_map.get(ext, "unknown")

        data = {
            "workspace": {
                "name": workspace_name or "Unknown Workspace",
                "path": "UNAVAILABLE" # Explicit read-only boundary
            },
            "active_file": {
                "name": file_name or "UNAVAILABLE",
                "language": language,
                "extension": ext
            },
            "window": {
                "title": title
            },
            "diagnostics": {
                "summary": "UNAVAILABLE"
            }
        }

        has_file = file_name != ""
        status = ContextStatus.AVAILABLE if has_file else ContextStatus.PARTIAL
        confidence = ContextConfidence.HIGH_CONFIDENCE if has_file else ContextConfidence.PARTIAL

        return ApplicationContext(
            adapter_id=self.adapter_id,
            application="vscode",
            classification=AppClassification.CODE_EDITOR,
            timestamp=int(time.time() * 1000),
            status=status,
            confidence=confidence,
            privacy=PrivacyLevel.PRIVATE,
            capabilities=["workspace", "active_file", "language"],
            data=data
        )

    def _parse_vscode_title(self, title: str) -> Tuple[str, str]:
        # Typical format: "filename.ext - workspace_name - Visual Studio Code"
        parts = [p.strip() for p in title.split(" - ") if p.strip()]
        if len(parts) >= 3:
            return parts[0], parts[1]
        elif len(parts) == 2:
            return parts[0], ""
        elif len(parts) == 1:
            return parts[0], ""
        return "", ""
