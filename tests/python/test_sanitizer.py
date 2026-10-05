from agent.execution.authorization import auth_service
"""
JARVIS Python Agent Core — Sanitizer & Security Unit Tests
"""

import pytest
from agent.proposals.sanitizer import ProposalSanitizer

def test_valid_proposal_sanitization():
    raw_prop = {
        "id": "prop_test_1",
        "workspaceId": "checkout",
        "baseRevision": 1,
        "title": "Valid Proposal",
        "reason": "Test reason",
        "operations": [
            {
                "op": "UPDATE_ELEMENT",
                "targetId": "btn_pay",
                "proposedValue": {"w": 300},
                "reason": "Update width"
            }
        ],
        "createdAt": 1000,
        "source": "AI",
        "status": "PENDING"
    }

    valid, clean, err = ProposalSanitizer.sanitize(raw_prop, known_element_ids=["btn_pay"])
    assert valid is True
    assert clean is not None
    assert err is None
    assert clean["operations"][0]["targetId"] == "btn_pay"

def test_disallowed_operation_type():
    raw_prop = {
        "id": "prop_test_2",
        "workspaceId": "checkout",
        "baseRevision": 1,
        "title": "Invalid Op",
        "reason": "Test reason",
        "operations": [
            {
                "op": "EXECUTE_SHELL_SCRIPT",
                "targetId": "btn_pay",
                "proposedValue": {},
                "reason": "Malicious op"
            }
        ],
        "createdAt": 1000,
        "source": "AI",
        "status": "PENDING"
    }

    valid, clean, err = ProposalSanitizer.sanitize(raw_prop, known_element_ids=["btn_pay"])
    assert valid is False
    assert clean is None
    assert "Disallowed operation type" in err

test_unknown_target_id = None
def test_unknown_target_id():
    raw_prop = {
        "id": "prop_test_3",
        "workspaceId": "checkout",
        "baseRevision": 1,
        "title": "Unknown Target",
        "reason": "Test reason",
        "operations": [
            {
                "op": "UPDATE_ELEMENT",
                "targetId": "nonexistent_element",
                "proposedValue": {},
                "reason": "Bad target"
            }
        ],
        "createdAt": 1000,
        "source": "AI",
        "status": "PENDING"
    }

    valid, clean, err = ProposalSanitizer.sanitize(raw_prop, known_element_ids=["btn_pay"])
    assert valid is False
    assert "targets unknown element ID" in err

def test_code_injection_rejection():
    raw_prop = {
        "id": "prop_test_4",
        "workspaceId": "checkout",
        "baseRevision": 1,
        "title": "Code Injection",
        "reason": "Test reason",
        "operations": [
            {
                "op": "UPDATE_ELEMENT",
                "targetId": "btn_pay",
                "proposedValue": {"label": "<script>alert(1)</script>"},
                "reason": "Malicious payload"
            }
        ],
        "createdAt": 1000,
        "source": "AI",
        "status": "PENDING"
    }

    valid, clean, err = ProposalSanitizer.sanitize(raw_prop, known_element_ids=["btn_pay"])
    assert valid is False
    assert "Forbidden injection pattern" in err
