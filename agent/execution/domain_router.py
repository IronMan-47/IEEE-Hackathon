"""
JARVIS Python Agent Core — Domain Router
Routes approved execution requests to domain-specific executors based on proposal domain.
Rejects unsupported domains (browser, terminal, figma, unknown, arbitrary) deterministically.
"""

from typing import Dict, Optional, Set
from agent.execution.base import BaseDomainExecutor
from agent.execution.living_canvas_executor import LivingCanvasExecutor
from agent.execution.vscode_executor import VSCodeExecutor
from agent.execution.browser_executor import BrowserExecutor
from agent.core.logging import logger

ALLOWED_DOMAINS: Set[str] = {"living_canvas", "vscode", "browser"}


class DomainRouter:
    def __init__(self):
        self._executors: Dict[str, BaseDomainExecutor] = {
            "living_canvas": LivingCanvasExecutor(),
            "vscode": VSCodeExecutor(),
            "browser": BrowserExecutor()
        }

    def get_executor(self, domain: str) -> Optional[BaseDomainExecutor]:
        d = (domain or "").lower().strip()
        if d not in ALLOWED_DOMAINS:
            logger.warn(f"DomainRouter REJECTED unsupported domain: '{d}'")
            return None
        return self._executors.get(d)

    def is_domain_supported(self, domain: str) -> bool:
        return (domain or "").lower().strip() in ALLOWED_DOMAINS
