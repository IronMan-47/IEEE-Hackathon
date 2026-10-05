import time
from typing import Optional, Callable
from agent.perception.types import PerceptionResult, CaptureMetadata
from agent.perception.active_window import WindowProvider, WindowsWindowProvider, MockWindowProvider
from agent.perception.screen import ScreenProvider, WindowsScreenProvider, MockScreenProvider
from agent.perception.classifier import AppClassifier
from agent.perception.policy import PerceptionPolicyManager

class CaptureManager:
    def __init__(
        self,
        window_provider: Optional[WindowProvider] = None,
        screen_provider: Optional[ScreenProvider] = None,
        policy_manager: Optional[PerceptionPolicyManager] = None,
        is_system_ready_fn: Optional[Callable[[], bool]] = None
    ):
        self.window_provider = window_provider or WindowsWindowProvider()
        self.screen_provider = screen_provider or WindowsScreenProvider()
        self.policy_manager = policy_manager or PerceptionPolicyManager()
        self.is_system_ready_fn = is_system_ready_fn or (lambda: True)

    def perceive_desktop(self, request_capture: bool = True) -> PerceptionResult:
        timestamp = int(time.time() * 1000)

        # 1. Emergency Stop Barrier
        if not self.is_system_ready_fn():
            return PerceptionResult(
                timestamp=timestamp,
                perception_enabled=False,
                capture_metadata=CaptureMetadata(captured=False)
            )

        # 2. Check Global Policy
        if not self.policy_manager.is_enabled():
            return PerceptionResult(
                timestamp=timestamp,
                perception_enabled=False,
                capture_metadata=CaptureMetadata(captured=False)
            )

        # 3. Detect Active Window & Screen Metadata
        app_id, win_info, screen_info = self.window_provider.get_active_window()

        # 4. Check Privacy Exclusions
        is_excluded = self.policy_manager.is_excluded(app_id.process_name)

        # 5. Classify Application
        classification = AppClassifier.classify(app_id.process_name, win_info.title)

        # 6. Screen Capture (if requested and allowed)
        capture_metadata = CaptureMetadata(captured=False)
        if request_capture and not is_excluded:
            bbox = (win_info.x, win_info.y, win_info.width, win_info.height)
            capture_metadata = self.screen_provider.capture_window(bbox)
            capture_metadata.timestamp = timestamp

        return PerceptionResult(
            timestamp=timestamp,
            active_application=app_id,
            active_window=win_info,
            screen_metadata=screen_info,
            capture_metadata=capture_metadata,
            classification=classification,
            perception_enabled=True,
            is_excluded=is_excluded
        )
