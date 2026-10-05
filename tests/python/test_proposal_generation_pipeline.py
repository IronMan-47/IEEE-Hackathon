from agent.execution.authorization import auth_service
"""
JARVIS Python Agent Core — Phase 9 Comprehensive Proposal Pipeline Tests
"""

import pytest
from agent.intent.models import (
    RequestNormalizer,
    Plan,
    PlanStep,
    PlanStepType,
    PlanStatus,
    Goal,
    TargetType,
    IntentCategory
)
from agent.proposals.models import (
    Proposal,
    ProposalOperation,
    ProposalStatus,
    RiskLevel
)
from agent.context.relevance_filter import ContextRelevanceFilter
from agent.proposals.validator import ProposalValidator
from agent.proposals.generator import ProposalGenerator
from agent.core.agent import JarvisAgent


def test_proposal_model_and_status():
    prop = Proposal(
        request_id="req_1",
        plan_id="plan_1",
        domain="living_canvas",
        base_context_id="ctx_1",
        base_context_hash="abc1234567890123",
        base_revision=2,
        title="Test Proposal",
        summary="Summary test",
        reason="Reason test",
        operations=[
            ProposalOperation(
                operation_id="op_1",
                op_type="UPDATE_STYLE",
                target="btn_pay",
                parameters={"style": {"fill": "#0284c7"}},
                reason="Enhance CTA color"
            )
        ]
    )
    assert prop.status == ProposalStatus.DRAFT
    assert prop.is_expired() is False
    assert prop.is_stale("abc1234567890123") is False
    assert prop.is_stale("different_hash_123") is True


def test_proposal_generation_living_canvas():
    agent = JarvisAgent()
    perception = {
        "active_window": {"title": "Living Canvas Reference App"},
        "active_application": {"name": "electron.exe"},
        "application_context": {"domain": "living_canvas", "extracted_fields": {"workspace_name": "Living Canvas"}}
    }
    plan, _, _, _, _ = agent.plan_request(
        raw_text="Make the primary CTA button more prominent",
        perception_context=perception
    )
    proposal, context = agent.generate_proposal_from_plan(plan, perception_context=perception)

    assert proposal.domain == "living_canvas"
    assert proposal.status == ProposalStatus.VALIDATED
    assert proposal.risk == RiskLevel.LOW
    assert len(proposal.operations) == 1
    assert proposal.operations[0].op_type == "UPDATE_STYLE"
    assert proposal.trace["plan_id"] == plan.plan_id


def test_proposal_generation_vscode():
    agent = JarvisAgent()
    perception = {
        "active_window": {"title": "agent.py - JARVIS - Visual Studio Code"},
        "active_application": {"name": "Code.exe"},
        "application_context": {"domain": "vscode", "extracted_fields": {"active_file": "agent.py", "language": "python"}}
    }
    plan, _, _, _, _ = agent.plan_request(
        raw_text="Refactor exception handling in agent.py",
        perception_context=perception
    )
    proposal, context = agent.generate_proposal_from_plan(plan, perception_context=perception)

    assert proposal.domain == "vscode"
    assert proposal.status == ProposalStatus.VALIDATED
    assert proposal.operations[0].op_type == "CODE_CHANGE"
    assert proposal.operations[0].target == "active_file.py"


def test_proposal_sanitizer_code_injection_rejection():
    rel_ctx = ContextRelevanceFilter.filter({}, {})
    unsafe_prop = Proposal(
        request_id="req_1",
        plan_id="plan_1",
        domain="living_canvas",
        base_context_id=rel_ctx.context_id,
        base_context_hash=rel_ctx.context_hash,
        title="Unsafe Proposal",
        summary="Test",
        reason="Test",
        operations=[
            ProposalOperation(
                operation_id="op_1",
                op_type="UPDATE_STYLE",
                target="btn_pay",
                parameters={"code": "import subprocess; subprocess.Popen('powershell.exe')"}, # Forbidden pattern!
                reason="Malicious code injection attempt"
            )
        ]
    )

    valid, err = ProposalValidator.validate(unsafe_prop, rel_ctx)
    assert valid is False
    assert "security violation" in err.lower() or "forbidden" in err.lower()


def test_stale_context_hash_detection():
    context1 = ContextRelevanceFilter.filter({"application_context": {"domain": "vscode", "extracted_fields": {"active_file": "fileA.py"}}}, {})
    context2 = ContextRelevanceFilter.filter({"application_context": {"domain": "vscode", "extracted_fields": {"active_file": "fileB.py"}}}, {})

    prop = Proposal(
        request_id="req_1",
        plan_id="plan_1",
        domain="vscode",
        base_context_id=context1.context_id,
        base_context_hash=context1.context_hash,
        title="Stale Test",
        summary="Test",
        reason="Test",
        operations=[ProposalOperation(operation_id="op_1", op_type="REFACTOR", target="fileA.py", reason="Refactor")]
    )

    # Valid against context1
    valid1, _ = ProposalValidator.validate(prop, context1)
    assert valid1 is True

    # Invalid / Stale against context2
    valid2, err2 = ProposalValidator.validate(prop, context2)
    assert valid2 is False
    assert "stale" in err2.lower()


def test_proposal_modification_immutability():
    rel_ctx = ContextRelevanceFilter.filter({}, {})
    p1 = Proposal(
        request_id="req_1",
        plan_id="plan_1",
        domain="living_canvas",
        base_context_id=rel_ctx.context_id,
        base_context_hash=rel_ctx.context_hash,
        title="Original Proposal",
        summary="Original summary",
        reason="Reason",
        operations=[ProposalOperation(operation_id="op_1", op_type="UPDATE_STYLE", target="btn_pay", parameters={"w": 300}, reason="Test")]
    )
    ProposalValidator.validate(p1, rel_ctx)

    new_ops = [
        ProposalOperation(operation_id="op_1", op_type="UPDATE_STYLE", target="btn_pay", parameters={"w": 360, "style": {"fill": "#059669"}}, reason="Human edit")
    ]

    p2 = ProposalGenerator.modify_proposal(p1, new_ops, rel_ctx, user_reason="Increased button width to 360px")

    assert p1.status == ProposalStatus.MODIFIED
    assert p2.version == p1.version + 1
    assert p2.parent_proposal_id == p1.proposal_id
    assert p2.source == "HUMAN_MODIFIED"
    assert p2.status == ProposalStatus.READY_FOR_REVIEW


def test_risk_classification():
    rel_ctx = ContextRelevanceFilter.filter({}, {})
    prop_low = Proposal(
        request_id="r1", plan_id="p1", domain="living_canvas",
        base_context_id=rel_ctx.context_id, base_context_hash=rel_ctx.context_hash,
        title="Low risk", summary="s", reason="r",
        operations=[ProposalOperation(operation_id="o1", op_type="UPDATE_STYLE", target="btn_pay", reason="style")]
    )
    ProposalValidator.validate(prop_low, rel_ctx)
    assert prop_low.risk == RiskLevel.LOW

    prop_high = Proposal(
        request_id="r2", plan_id="p2", domain="living_canvas",
        base_context_id=rel_ctx.context_id, base_context_hash=rel_ctx.context_hash,
        title="High risk", summary="s", reason="r",
        operations=[ProposalOperation(operation_id="o2", op_type="REMOVE_ELEMENT", target="btn_pay", reason="delete")]
    )
    ProposalValidator.validate(prop_high, rel_ctx)
    assert prop_high.risk == RiskLevel.HIGH


def test_proposal_acceptance_no_execution():
    agent = JarvisAgent()
    perception = {
        "application_context": {"domain": "living_canvas", "extracted_fields": {"workspace_name": "Living Canvas"}}
    }
    plan, _, _, _, _ = agent.plan_request("Make primary CTA prominent", perception_context=perception)
    proposal, context = agent.generate_proposal_from_plan(plan, perception_context=perception)

    accepted_prop, token, _ = agent.accept_proposal_phase9(proposal, perception_context=perception)

    assert accepted_prop.status == ProposalStatus.ACCEPTED
    assert "token_id" in token
    assert token["proposal_id"] == proposal.proposal_id
    # Critical guarantee: base_revision remains unchanged (0)
    assert accepted_prop.base_revision == 0
