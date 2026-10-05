from typing import List, Optional, Dict, Any
from agent.perception.types import PerceptionResult
from agent.adapters.base import BaseAdapter, ApplicationContext
from agent.adapters.sanitizer import ContextSanitizer
from agent.adapters.living_canvas.adapter import LivingCanvasAdapter
from agent.adapters.vscode.adapter import VSCodeAdapter
from agent.adapters.browser.adapter import BrowserAdapter
from agent.adapters.terminal.adapter import TerminalAdapter
from agent.adapters.figma.adapter import FigmaAdapter
from agent.adapters.unknown.adapter import UnknownAdapter

class AdapterRegistry:
    def __init__(self):
        self._adapters: List[BaseAdapter] = []
        self._register_default_adapters()

    def register(self, adapter: BaseAdapter) -> None:
        # Prevent duplicate adapter ID registration
        if any(a.adapter_id == adapter.adapter_id for a in self._adapters):
            return
        self._adapters.append(adapter)

    def resolve(self, perception: PerceptionResult) -> BaseAdapter:
        for adapter in self._adapters:
            # Skip unknown adapter during first loop pass
            if adapter.adapter_id == "unknown":
                continue
            if adapter.can_handle(perception):
                return adapter
        return UnknownAdapter()

    def get_application_context(
        self,
        perception: PerceptionResult,
        workspace_context: Optional[Dict[str, Any]] = None,
        mock_data: Optional[Dict[str, Any]] = None
    ) -> ApplicationContext:
        adapter = self.resolve(perception)

        if adapter.adapter_id == "living_canvas":
            ctx = adapter.get_context(perception, workspace_context=workspace_context)
        elif mock_data and hasattr(adapter, "get_context"):
            ctx = adapter.get_context(perception, mock_data=mock_data)
        else:
            ctx = adapter.get_context(perception)

        # Pass context through safety sanitizer
        sanitized_ctx = ContextSanitizer.sanitize(ctx)
        return sanitized_ctx

    def _register_default_adapters(self) -> None:
        self.register(LivingCanvasAdapter())
        self.register(VSCodeAdapter())
        self.register(BrowserAdapter())
        self.register(TerminalAdapter())
        self.register(FigmaAdapter())
        self.register(UnknownAdapter())
