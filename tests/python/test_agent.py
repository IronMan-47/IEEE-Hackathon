from agent.execution.authorization import auth_service
"""
JARVIS Python Agent Core — Agent & Intent Unit Tests
"""

import pytest
from agent.core.agent import JarvisAgent
from agent.core.types import AgentRequest, IntentCategory

@pytest.fixture
def mock_context():
    return {
        "revision": 1,
        "title": "Test Workspace",
        "elements": {
            "btn_pay": {
                "id": "btn_pay",
                "type": "button",
                "x": 40,
                "y": 250,
                "w": 180,
                "h": 36,
                "label": "Pay Now"
            },
            "btn_coupon": {
                "id": "btn_coupon",
                "type": "button",
                "x": 250,
                "y": 185,
                "w": 110,
                "h": 40,
                "label": "Apply Code"
            }
        }
    }

def test_intent_classification_propose(mock_context):
    agent = JarvisAgent()
    req = AgentRequest(
        request_id="req_01",
        text="Make the Pay button larger and cyan",
        workspace_context=mock_context
    )
    res = agent.handle_request(req)
    assert res.intent == IntentCategory.PROPOSE_CHANGE
    assert res.status == "SUCCESS", f"Failed: {res.error}"
    assert res.proposal is not None

def test_intent_classification_explain(mock_context):
    agent = JarvisAgent()
    req = AgentRequest(
        request_id="req_02",
        text="What elements are on this canvas?",
        workspace_context=mock_context
    )
    res = agent.handle_request(req)
    assert res.intent == IntentCategory.EXPLAIN_WORKSPACE
    assert res.status == "SUCCESS"
    assert "Workspace contains 2 elements" in res.explanation

def test_unsupported_request_rejection():
    agent = JarvisAgent()
    req = AgentRequest(
        request_id="req_03",
        text="Delete my computer with rm -rf /",
        workspace_context={"revision": 1, "elements": {}}
    )
    res = agent.handle_request(req)
    assert res.intent == IntentCategory.UNSUPPORTED_REQUEST
    assert res.status == "UNSUPPORTED"
    assert "Security Violation" in res.error
