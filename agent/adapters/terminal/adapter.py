import time
from typing import Dict, Any, Optional
from agent.perception.types import AppClassification, PerceptionResult
from agent.adapters.base import BaseAdapter, ApplicationContext, PrivacyLevel, ContextStatus, ContextConfidence

class TerminalAdapter(BaseAdapter):
    adapter_id = "terminal"
    supported_classifications = [AppClassification.TERMINAL]

    def can_handle(self, perception: PerceptionResult) -> bool:
        proc = (perception.active_application.process_name or "").lower()
        title = (perception.active_window.title or "").lower()
        terminals = {"cmd.exe", "powershell.exe", "wt.exe", "bash.exe", "zsh.exe", "conhost.exe", "windowsterminal.exe"}
        return proc in terminals or "powershell" in title or "command prompt" in title or "terminal" in title

    def get_context(self, perception: PerceptionResult, mock_data: Optional[Dict[str, Any]] = None) -> ApplicationContext:
        if mock_data:
            return ApplicationContext(
                adapter_id=self.adapter_id,
                application=f"terminal.{perception.active_application.name.lower()}",
                classification=AppClassification.TERMINAL,
                timestamp=int(time.time() * 1000),
                status=ContextStatus.AVAILABLE,
                confidence=ContextConfidence.HIGH_CONFIDENCE,
                privacy=PrivacyLevel.PRIVATE,
                capabilities=["shell_type", "window_title"],
                data=mock_data
            )

        proc = perception.active_application.process_name.lower()
        shell_type = "PowerShell" if "powershell" in proc else "Command Prompt" if "cmd" in proc else "Windows Terminal" if "wt" in proc else "Bash"

        data = {
            "terminal": perception.active_application.name,
            "shell": shell_type,
            "window_title": perception.active_window.title,
            "working_directory": "UNAVAILABLE" # Explicit Read-Only boundary
        }

        return ApplicationContext(
            adapter_id=self.adapter_id,
            application=f"terminal.{shell_type.lower().replace(' ', '_')}",
            classification=AppClassification.TERMINAL,
            timestamp=int(time.time() * 1000),
            status=ContextStatus.PARTIAL,
            confidence=ContextConfidence.HIGH_CONFIDENCE,
            privacy=PrivacyLevel.PRIVATE,
            capabilities=["shell_type", "window_title"],
            data=data
        )
