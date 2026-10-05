import time
from typing import Dict, Any, Optional
from agent.perception.types import AppClassification, PerceptionResult
from agent.adapters.base import BaseAdapter, ApplicationContext, PrivacyLevel, ContextStatus, ContextConfidence

class BrowserAdapter(BaseAdapter):
    adapter_id = "browser"
    supported_classifications = [AppClassification.BROWSER]

    def can_handle(self, perception: PerceptionResult) -> bool:
        proc = (perception.active_application.process_name or "").lower()
        title = (perception.active_window.title or "").lower()
        browsers = {"chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe", "vivaldi.exe"}
        return proc in browsers or "chrome" in title or "edge" in title or "firefox" in title

    def get_context(self, perception: PerceptionResult, mock_data: Optional[Dict[str, Any]] = None) -> ApplicationContext:
        if mock_data:
            return ApplicationContext(
                adapter_id=self.adapter_id,
                application=f"browser.{perception.active_application.name.lower()}",
                classification=AppClassification.BROWSER,
                timestamp=int(time.time() * 1000),
                status=ContextStatus.AVAILABLE,
                confidence=ContextConfidence.HIGH_CONFIDENCE,
                privacy=PrivacyLevel.PRIVATE,
                capabilities=["page_title", "browser_type"],
                data=mock_data
            )

        title = perception.active_window.title or ""
        page_title, browser_name = self._parse_browser_title(title)

        data = {
            "browser": browser_name or perception.active_application.name,
            "page_title": page_title or "Browser Workspace",
            "active_url": "UNAVAILABLE", # Explicit Privacy Boundary: Read-only title inspection
            "domain": "UNAVAILABLE",
            "privacy": "PROTECTED"
        }

        return ApplicationContext(
            adapter_id=self.adapter_id,
            application=f"browser.{perception.active_application.name.lower()}",
            classification=AppClassification.BROWSER,
            timestamp=int(time.time() * 1000),
            status=ContextStatus.PARTIAL,
            confidence=ContextConfidence.PARTIAL,
            privacy=PrivacyLevel.PRIVATE,
            capabilities=["page_title", "browser_type"],
            data=data
        )

    def _parse_browser_title(self, title: str) -> tuple[str, str]:
        parts = [p.strip() for p in title.split(" - ") if p.strip()]
        if len(parts) >= 2:
            return " - ".join(parts[:-1]), parts[-1]
        elif len(parts) == 1:
            return parts[0], ""
        return "", ""
