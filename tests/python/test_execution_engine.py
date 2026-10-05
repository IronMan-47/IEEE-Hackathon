from agent.execution.authorization import auth_service
"""
JARVIS Python Agent Core — Phase 10 Comprehensive Execution Engine Tests
"""

import pytest
from datetime import datetime, timezone, timedelta
from agent.execution.models import ExecutionRequest, ExecutionStatus
from agent.proposals.models import Proposal, ProposalOperation, ProposalStatus, RiskLevel
from agent.context.relevance_filter import ContextRelevanceFilter
from agent.execution.living_canvas_executor import LivingCanvasExecutor
from agent.execution.safety_barrier import ExecutionSafetyBarrier
from agent.core.agent import JarvisAgent


def test_successful_living_canvas_execution():
    executor = LivingCanvasExecutor()
    rel_ctx = ContextRelevanceFilter.filter({"application_context": {"domain": "living_canvas"}}, {"revision": 4})

    proposal = Proposal(
        request_id="req_1", plan_id="plan_1", domain="living_canvas",
        base_context_id=rel_ctx.context_id, base_context_hash=rel_ctx.context_hash,
        base_revision=4, title="Test Exec", summary="s", reason="r",
        operations=[
            ProposalOperation(operation_id="op_1", op_type="UPDATE_STYLE", target="btn_pay", parameters={"w": 320, "style": {"fill": "#06B6D4"}}, reason="r")
        ]
    )

    token = {
        "tokenId": "token_valid_100",
        "proposalId": proposal.proposal_id,
        "baseRevision": 4,
        "contextHash": rel_ctx.context_hash,
        "expiresAt": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    }

    exec_req = ExecutionRequest(
        proposal_id=proposal.proposal_id,
        approval_token=auth_service.generate_token(proposal),
        base_revision=4,
        base_context_id=rel_ctx.context_id,
        base_context_hash=rel_ctx.context_hash
    )

    ws_context = {"revision": 4, "elements": {"btn_pay": {"id": "btn_pay", "type": "button", "w": 180}}}

    res = executor.execute(exec_req, proposal, rel_ctx, workspace_context=ws_context)

    assert res.status == ExecutionStatus.COMMITTED
    assert res.verification == "PASSED"
    assert res.previous_revision == 4
    assert res.new_revision == 5
    assert res.version_id is not None
    assert len(res.operations_applied) == 1


def test_emergency_stop_blocked_execution():
    executor = LivingCanvasExecutor()
    rel_ctx = ContextRelevanceFilter.filter({}, {"revision": 2})

    proposal = Proposal(
        request_id="req_1", plan_id="plan_1", domain="living_canvas",
        base_context_id=rel_ctx.context_id, base_context_hash=rel_ctx.context_hash,
        base_revision=2, title="Test Exec", summary="s", reason="r",
        operations=[ProposalOperation(operation_id="op_1", op_type="UPDATE_STYLE", target="btn_pay", reason="r")]
    )
    token = auth_service.generate_token(proposal)
    exec_req = ExecutionRequest(proposal_id=proposal.proposal_id, approval_token=auth_service.generate_token(proposal), base_revision=2, base_context_id=rel_ctx.context_id, base_context_hash=rel_ctx.context_hash)

    # is_system_ready = False (Emergency Stop ACTIVE)
    from agent.runtime.lifecycle import runtime_manager
    runtime_manager.state.emergency_stop_state = True
    try:
        res = executor.execute(exec_req, proposal, rel_ctx, workspace_context={"revision": 2})
    finally:
        runtime_manager.state.emergency_stop_state = False

    assert res.status == ExecutionStatus.BLOCKED
    assert "Emergency Stop" in res.error


def test_unsupported_domain_execution_rejection():
    agent = JarvisAgent()
    rel_ctx = ContextRelevanceFilter.filter({"application_context": {"domain": "terminal"}}, {"revision": 1})

    proposal = Proposal(
        request_id="req_1", plan_id="plan_1", domain="terminal",
        base_context_id=rel_ctx.context_id, base_context_hash=rel_ctx.context_hash,
        base_revision=1, title="Terminal Proposal", summary="s", reason="r",
        operations=[ProposalOperation(operation_id="op_1", op_type="TERMINAL_INSPECT", target="sh", reason="r")]
    )
    token = {"tokenId": "tok_2", "proposalId": proposal.proposal_id, "baseRevision": 1, "contextHash": rel_ctx.context_hash}
    exec_req = ExecutionRequest(proposal_id=proposal.proposal_id, approval_token=auth_service.generate_token(proposal), base_revision=1, base_context_id=rel_ctx.context_id, base_context_hash=rel_ctx.context_hash)

    res = agent.execute_proposal(exec_req, proposal, perception_context={"application_context": {"domain": "terminal"}}, workspace_context={"revision": 1})

    assert res.status == ExecutionStatus.BLOCKED
    assert "UNAVAILABLE" in res.error


def test_stale_revision_execution_rejection():
    executor = LivingCanvasExecutor()
    rel_ctx = ContextRelevanceFilter.filter({"application_context": {"domain": "living_canvas"}}, {"revision": 4})

    proposal = Proposal(
        request_id="req_1", plan_id="plan_1", domain="living_canvas",
        base_context_id=rel_ctx.context_id, base_context_hash=rel_ctx.context_hash,
        base_revision=4, title="Test", summary="s", reason="r",
        operations=[ProposalOperation(operation_id="op_1", op_type="UPDATE_STYLE", target="btn_pay", reason="r")]
    )
    token = {"tokenId": "tok_stale_1", "proposalId": proposal.proposal_id, "baseRevision": 4, "contextHash": rel_ctx.context_hash}
    exec_req = ExecutionRequest(proposal_id=proposal.proposal_id, approval_token=auth_service.generate_token(proposal), base_revision=4, base_context_id=rel_ctx.context_id, base_context_hash=rel_ctx.context_hash)

    # Workspace revision bumped to 5 (stale proposal)
    res = executor.execute(exec_req, proposal, rel_ctx, workspace_context={"revision": 5})

    assert res.status == ExecutionStatus.BLOCKED
    assert "STALE_PROPOSAL" in res.error


def test_token_replay_attack_prevention():
    executor = LivingCanvasExecutor()
    rel_ctx = ContextRelevanceFilter.filter({"application_context": {"domain": "living_canvas"}}, {"revision": 1})

    proposal = Proposal(
        request_id="req_1", plan_id="plan_1", domain="living_canvas",
        base_context_id=rel_ctx.context_id, base_context_hash=rel_ctx.context_hash,
        base_revision=1, title="Test", summary="s", reason="r",
        operations=[ProposalOperation(operation_id="op_1", op_type="UPDATE_STYLE", target="btn_pay", reason="r")]
    )
    token = {"tokenId": "token_replay_999", "proposalId": proposal.proposal_id, "baseRevision": 1, "contextHash": rel_ctx.context_hash}
    exec_req = ExecutionRequest(proposal_id=proposal.proposal_id, approval_token=auth_service.generate_token(proposal), base_revision=1, base_context_id=rel_ctx.context_id, base_context_hash=rel_ctx.context_hash)
    ws_ctx = {"revision": 1, "elements": {"btn_pay": {"id": "btn_pay"}}}

    # First execution succeeds
    res1 = executor.execute(exec_req, proposal, rel_ctx, workspace_context=ws_ctx)
    assert res1.status == ExecutionStatus.COMMITTED

    # Replay attempt with same token fails
    res2 = executor.execute(exec_req, proposal, rel_ctx, workspace_context=ws_ctx)
    assert res2.status == ExecutionStatus.BLOCKED
    assert "UNAUTHORIZED" in res2.error


def test_execution_atomicity_failure_rollback():
    executor = LivingCanvasExecutor()
    rel_ctx = ContextRelevanceFilter.filter({"application_context": {"domain": "living_canvas"}}, {"revision": 1})

    proposal = Proposal(
        request_id="req_1", plan_id="plan_1", domain="living_canvas",
        base_context_id=rel_ctx.context_id, base_context_hash=rel_ctx.context_hash,
        base_revision=1, title="Atomic Test", summary="s", reason="r",
        operations=[
            ProposalOperation(operation_id="op_1", op_type="UPDATE_STYLE", target="btn_pay", parameters={"w": 300}, reason="r"),
            ProposalOperation(operation_id="op_2", op_type="UPDATE_STYLE", target="non_existent_element", parameters={"w": 300}, reason="r") # Fails!
        ]
    )
    token = {"tokenId": "token_atomic_1", "proposalId": proposal.proposal_id, "baseRevision": 1, "contextHash": rel_ctx.context_hash}
    exec_req = ExecutionRequest(proposal_id=proposal.proposal_id, approval_token=auth_service.generate_token(proposal), base_revision=1, base_context_id=rel_ctx.context_id, base_context_hash=rel_ctx.context_hash)
    ws_ctx = {"revision": 1, "elements": {"btn_pay": {"id": "btn_pay", "w": 180}}}

    res = executor.execute(exec_req, proposal, rel_ctx, workspace_context=ws_ctx)

    assert res.status == ExecutionStatus.FAILED
    assert "not found" in res.error.lower()
    # Workspace revision remains unchanged at 1
    assert res.new_revision == 1


def test_security_primitive_barrier():
    executor = LivingCanvasExecutor()
    rel_ctx = ContextRelevanceFilter.filter({"application_context": {"domain": "living_canvas"}}, {"revision": 1})

    unsafe_prop = Proposal(
        request_id="req_1", plan_id="plan_1", domain="living_canvas",
        base_context_id=rel_ctx.context_id, base_context_hash=rel_ctx.context_hash,
        base_revision=1, title="Unsafe Exec", summary="s", reason="r",
        operations=[
            ProposalOperation(operation_id="op_1", op_type="UPDATE_STYLE", target="btn_pay", parameters={"run_command": "powershell.exe"}, reason="r")
        ]
    )
    token = auth_service.generate_token(unsafe_prop)
    exec_req = ExecutionRequest(proposal_id=unsafe_prop.proposal_id, approval_token=token, base_revision=1, base_context_id=rel_ctx.context_id, base_context_hash=rel_ctx.context_hash)

    res = executor.execute(exec_req, unsafe_prop, rel_ctx, workspace_context={"revision": 1})

    assert res.status == ExecutionStatus.BLOCKED
    assert "SAFETY_BARRIER_VIOLATION" in res.error or "primitive" in res.error
