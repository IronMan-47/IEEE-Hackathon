from agent.adapters.base import (
    BaseAdapter,
    ApplicationContext,
    PrivacyLevel,
    ContextStatus,
    ContextConfidence
)
from agent.adapters.sanitizer import ContextSanitizer
from agent.adapters.registry import AdapterRegistry
from agent.adapters.living_canvas.adapter import LivingCanvasAdapter
from agent.adapters.vscode.adapter import VSCodeAdapter
from agent.adapters.browser.adapter import BrowserAdapter
from agent.adapters.terminal.adapter import TerminalAdapter
from agent.adapters.figma.adapter import FigmaAdapter
from agent.adapters.unknown.adapter import UnknownAdapter

__all__ = [
    "BaseAdapter",
    "ApplicationContext",
    "PrivacyLevel",
    "ContextStatus",
    "ContextConfidence",
    "ContextSanitizer",
    "AdapterRegistry",
    "LivingCanvasAdapter",
    "VSCodeAdapter",
    "BrowserAdapter",
    "TerminalAdapter",
    "FigmaAdapter",
    "UnknownAdapter"
]
