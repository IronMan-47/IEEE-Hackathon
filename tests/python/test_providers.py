from agent.execution.authorization import auth_service
"""
JARVIS Python Agent Core — LLM Provider Unit Tests
"""

import pytest
from agent.llm.mock_provider import MockProvider
from agent.context.workspace_context import WorkspaceContextModel

def test_mock_provider_success():
    provider = MockProvider()
    context = WorkspaceContextModel({"revision": 3, "elements": {"btn_pay": {}}})
    success, proposal, err = provider.generate_proposal(context, "Make button larger")

    assert success is True
    assert err is None
    assert proposal["baseRevision"] == 3
    assert len(proposal["operations"]) == 1
    assert proposal["operations"][0]["target"] == "btn_pay"

def test_mock_provider_simulated_error():
    provider = MockProvider()
    context = WorkspaceContextModel({"revision": 1, "elements": {}})
    success, proposal, err = provider.generate_proposal(context, "trigger_error")

    assert success is False
    assert proposal is None
    assert "Simulated LLM Provider Timeout" in err
