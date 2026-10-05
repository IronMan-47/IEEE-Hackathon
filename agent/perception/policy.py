from typing import List, Set

class PerceptionPolicyManager:
    def __init__(self, enabled: bool = True, excluded_apps: List[str] = None):
        self._enabled = enabled
        self._excluded_apps: Set[str] = {
            app.lower() for app in (excluded_apps or ["1password.exe", "keepass.exe", "bitwarden.exe"])
        }

    def is_enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def is_excluded(self, process_name: str) -> bool:
        if not process_name:
            return False
        return process_name.lower().strip() in self._excluded_apps

    def add_excluded_app(self, process_name: str) -> None:
        if process_name:
            self._excluded_apps.add(process_name.lower().strip())

    def remove_excluded_app(self, process_name: str) -> None:
        if process_name:
            self._excluded_apps.discard(process_name.lower().strip())

    def can_capture(self, process_name: str = "") -> bool:
        if not self._enabled:
            return False
        if process_name and self.is_excluded(process_name):
            return False
        return True
