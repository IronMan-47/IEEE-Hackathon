from agent.execution.authorization import auth_service
import pytest
from agent.context.cross_application import CrossAppHandoffManager, HandoffStatus
from agent.context.fusion.models import GroundedContext, AppInfo, ApplicationRole

@pytest.fixture
def mock_vscode_context():
    return GroundedContext(
        context_id="ctx_vs_123",
        context_hash="hash_abc",
        primary_application=AppInfo(name="Visual Studio Code")
    )

@pytest.fixture
def mock_browser_context():
    return GroundedContext(
        context_id="ctx_br_456",
        context_hash="hash_def",
        primary_application=AppInfo(name="Google Chrome")
    )

def test_create_handoff(mock_vscode_context):
    evidence = {"error": "ModuleNotFoundError", "config": "api_key='secret123'"}
    handoff = CrossAppHandoffManager.create_handoff(
        workflow_id="wf_1",
        source_app="vscode",
        target_app="browser",
        source_context=mock_vscode_context,
        relevant_evidence=evidence
    )
    
    assert handoff.source_context_id == "ctx_vs_123"
    assert handoff.target_application == "browser"
    assert handoff.handoff_status == HandoffStatus.SANITIZED
    assert "secret123" not in handoff.sanitized_payload["config"]

def test_verify_target_context_success(mock_vscode_context, mock_browser_context):
    handoff = CrossAppHandoffManager.create_handoff(
        workflow_id="wf_2",
        source_app="vscode",
        target_app="browser",
        source_context=mock_vscode_context,
        relevant_evidence={"query": "test"}
    )
    
    success = CrossAppHandoffManager.verify_target_context(handoff, mock_browser_context)
    
    assert success is True
    assert handoff.handoff_status == HandoffStatus.ACCEPTED
    assert handoff.target_context_id == "ctx_br_456"

def test_verify_target_context_failure_mismatch(mock_vscode_context):
    handoff = CrossAppHandoffManager.create_handoff(
        workflow_id="wf_3",
        source_app="vscode",
        target_app="browser",
        source_context=mock_vscode_context,
        relevant_evidence={"query": "test"}
    )
    
    # Simulate user opened discord instead of a browser
    wrong_context = GroundedContext(
        context_id="ctx_wrong_789",
        context_hash="hash_wrong",
        primary_application=AppInfo(name="Discord")
    )
    
    success = CrossAppHandoffManager.verify_target_context(handoff, wrong_context)
    
    assert success is False
    assert handoff.handoff_status == HandoffStatus.BLOCKED
