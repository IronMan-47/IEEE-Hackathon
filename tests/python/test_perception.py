from agent.execution.authorization import auth_service
import pytest
from agent.perception.types import AppClassification, PerceptionResult
from agent.perception.active_window import MockWindowProvider, WindowsWindowProvider
from agent.perception.screen import MockScreenProvider
from agent.perception.classifier import AppClassifier
from agent.perception.policy import PerceptionPolicyManager
from agent.perception.capture import CaptureManager
from agent.context.perception_context import ContextBuilder, ContextSource

def test_application_classifier():
    assert AppClassifier.classify("Code.exe", "main.py") == AppClassification.CODE_EDITOR
    assert AppClassifier.classify("chrome.exe", "Google") == AppClassification.BROWSER
    assert AppClassifier.classify("Figma.exe", "UI Design") == AppClassification.DESIGN_TOOL
    assert AppClassifier.classify("powershell.exe", "Terminal") == AppClassification.TERMINAL
    assert AppClassifier.classify("winword.exe", "Doc1") == AppClassification.DOCUMENT_EDITOR
    assert AppClassifier.classify("random_app.exe", "Random") == AppClassification.UNKNOWN

def test_mock_window_provider():
    provider = MockWindowProvider(scenario="VS_CODE")
    app, win, screen = provider.get_active_window()
    assert app.process_name == "Code.exe"
    assert "Visual Studio Code" in app.name
    assert "main.py" in win.title
    assert screen.primary_width == 1920

def test_mock_screen_provider():
    screen = MockScreenProvider(should_fail=False)
    cap = screen.capture_window((0, 0, 100, 100))
    assert cap.captured is True
    assert cap.data_base64 is not None

def test_perception_policy_manager():
    policy = PerceptionPolicyManager(enabled=True, excluded_apps=["1password.exe"])
    assert policy.is_enabled() is True
    assert policy.can_capture("1password.exe") is False
    assert policy.can_capture("code.exe") is True

    policy.set_enabled(False)
    assert policy.can_capture("code.exe") is False

def test_capture_manager_vs_code():
    capture_mgr = CaptureManager(
        window_provider=MockWindowProvider("VS_CODE"),
        screen_provider=MockScreenProvider(),
        policy_manager=PerceptionPolicyManager(enabled=True)
    )

    res = capture_mgr.perceive_desktop(request_capture=True)
    assert res.perception_enabled is True
    assert res.is_excluded is False
    assert res.classification == AppClassification.CODE_EDITOR
    assert res.active_application.process_name == "Code.exe"
    assert res.capture_metadata.captured is True

def test_capture_manager_excluded_application():
    capture_mgr = CaptureManager(
        window_provider=MockWindowProvider("VS_CODE"),
        screen_provider=MockScreenProvider(),
        policy_manager=PerceptionPolicyManager(enabled=True, excluded_apps=["Code.exe"])
    )

    res = capture_mgr.perceive_desktop(request_capture=True)
    assert res.is_excluded is True
    assert res.capture_metadata.captured is False # Screenshot blocked for excluded process

def test_capture_manager_emergency_stop_barrier():
    capture_mgr = CaptureManager(
        window_provider=MockWindowProvider("VS_CODE"),
        screen_provider=MockScreenProvider(),
        policy_manager=PerceptionPolicyManager(enabled=True),
        is_system_ready_fn=lambda: False # STOPPED state
    )

    res = capture_mgr.perceive_desktop(request_capture=True)
    assert res.perception_enabled is False
    assert res.capture_metadata.captured is False

def test_privacy_summary_dict_omits_b64():
    res = PerceptionResult(
        timestamp=123456,
        perception_enabled=True
    )
    res.capture_metadata.data_base64 = "SECRET_IMAGE_BYTES"

    summary = res.to_summary_dict()
    assert "data_base64" not in summary["capture_metadata"]

def test_context_builder():
    capture_mgr = CaptureManager(window_provider=MockWindowProvider("CHROME"))
    res = capture_mgr.perceive_desktop(request_capture=False)

    context = ContextBuilder.build_desktop_context(res)
    assert context["source"] == ContextSource.DESKTOP_PERCEPTION.value
    assert context["classification"] == AppClassification.BROWSER.value
    assert context["active_application"]["process_name"] == "chrome.exe"
