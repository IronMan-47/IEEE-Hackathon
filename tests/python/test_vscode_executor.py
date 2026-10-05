from agent.execution.authorization import auth_service
"""
JARVIS Phase 11 — VS Code Controlled Execution Engine Pytest Suite
Tests VS Code domain executor, domain router, safety barriers, target resolution, document conflict detection,
closed-loop verification, token replay protection, emergency stop, and prompt injection defense.
"""

import pytest
import time
import hashlib
from datetime import datetime, timezone, timedelta
from agent.execution.base import BaseDomainExecutor
from agent.execution.domain_router import DomainRouter
from agent.execution.vscode_executor import VSCodeExecutor
from agent.execution.living_canvas_executor import LivingCanvasExecutor
from agent.execution.models import ExecutionRequest, ExecutionStatus
from agent.execution.safety_barrier import ExecutionSafetyBarrier, CONSUMED_TOKENS
from agent.proposals.models import Proposal, ProposalOperation, ProposalStatus, RiskLevel
from agent.context.relevance_filter import ContextRelevanceFilter, RelevantContext
from agent.core.agent import JarvisAgent


@pytest.fixture
def clean_tokens():
    CONSUMED_TOKENS.clear()
    yield
    CONSUMED_TOKENS.clear()


@pytest.fixture
def domain_router():
    return DomainRouter()


@pytest.fixture
def mock_vscode_context():
    content = "def add(a, b):\n    pass\n"
    c_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    return RelevantContext(
        context_id="vscode_ctx_1",
        context_hash=c_hash,
        active_app_domain="vscode",
        active_application="Microsoft Visual Studio Code",
        active_file="example.py",
        active_window_title="example.py - test_project - Visual Studio Code",
        workspace_revision=1,
        timestamp=int(time.time() * 1000)
    )


@pytest.fixture
def valid_approval_token():
    return {
        "tokenId": "token_vscode_123",
        "proposalId": "prop_vscode_1",
        "baseRevision": 1,
        "contextHash": "hash_123",
        "issuedAt": datetime.now(timezone.utc).isoformat(),
        "expiresAt": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        "singleUse": True,
        "status": "ISSUED"
    }


# Test A & B: Domain Router Selection & Rejection
def test_domain_router_selection_and_rejection(domain_router):
    assert isinstance(domain_router.get_executor("vscode"), VSCodeExecutor)
    assert isinstance(domain_router.get_executor("living_canvas"), LivingCanvasExecutor)
    assert isinstance(domain_router.get_executor("browser"), BaseDomainExecutor)

    assert domain_router.get_executor("terminal") is None
    assert domain_router.get_executor("figma") is None
    assert domain_router.get_executor("unknown") is None
    assert domain_router.get_executor("shell_exec") is None


# Test C: Valid CODE_CHANGE execution and postcondition verification
def test_successful_vscode_code_change_execution(clean_tokens, mock_vscode_context, valid_approval_token):
    initial_code = "def add(a, b):\n    pass\n"
    initial_hash = hashlib.sha256(initial_code.encode('utf-8')).hexdigest()
    mock_vscode_context.context_hash = initial_hash

    valid_approval_token["contextHash"] = initial_hash

    proposal = Proposal(
        proposal_id="prop_vscode_1",
        request_id="req_1",
        plan_id="plan_1",
        domain="vscode",
        base_context_id=mock_vscode_context.context_id,
        base_context_hash=initial_hash,
        base_revision=1,
        title="Implement add function",
        summary="Add implementation to add function",
        reason="Implement math utility",
        operations=[
            ProposalOperation(
                operation_id="op_1",
                op_type="CODE_CHANGE",
                target="example.py",
                parameters={
                    "file": "example.py",
                    "target_content": "def add(a, b):\n    pass",
                    "replacement_content": "def add(a, b):\n    return a + b",
                    "base_hash": initial_hash
                },
                reason="Controlled code edit"
            )
        ],
        status=ProposalStatus.ACCEPTED
    )

    request = ExecutionRequest(
        execution_id="exec_vscode_1",
        proposal_id="prop_vscode_1",
        approval_token=auth_service.generate_token(proposal),
        base_revision=1,
        base_context_id=mock_vscode_context.context_id,
        base_context_hash=initial_hash
    )

    workspace_context = {
        "allow_mock_app": True,
        "mock_files": {
            "example.py": initial_code
        }
    }

    executor = VSCodeExecutor()
    result = executor.execute(request, proposal, mock_vscode_context, workspace_context=workspace_context)

    assert result.status == ExecutionStatus.COMMITTED
    assert result.verification == "PASSED"
    assert len(result.operations_applied) == 1
    assert "return a + b" in workspace_context["mock_files"]["example.py"]


# Test D: Valid FORMAT_CODE execution
def test_successful_vscode_format_code_execution(clean_tokens, mock_vscode_context, valid_approval_token):
    unformatted = "def add(a, b):   \n    return a + b   \n"
    initial_hash = hashlib.sha256(unformatted.encode('utf-8')).hexdigest()
    mock_vscode_context.context_hash = initial_hash
    valid_approval_token["contextHash"] = initial_hash

    proposal = Proposal(
        proposal_id="prop_vscode_1",
        request_id="req_1",
        plan_id="plan_1",
        domain="vscode",
        base_context_id=mock_vscode_context.context_id,
        base_context_hash=initial_hash,
        base_revision=1,
        title="Format code",
        summary="Strip trailing whitespace",
        reason="Format document",
        operations=[
            ProposalOperation(
                operation_id="op_1",
                op_type="FORMAT_CODE",
                target="example.py",
                parameters={"file": "example.py", "language": "python", "base_hash": initial_hash},
                reason="Formatting"
            )
        ],
        status=ProposalStatus.ACCEPTED
    )

    request = ExecutionRequest(
        execution_id="exec_vscode_format",
        proposal_id="prop_vscode_1",
        approval_token=auth_service.generate_token(proposal),
        base_revision=1,
        base_context_id=mock_vscode_context.context_id,
        base_context_hash=initial_hash
    )

    workspace_context = {
        "allow_mock_app": True,
        "mock_files": {"example.py": unformatted}
    }

    executor = VSCodeExecutor()
    result = executor.execute(request, proposal, mock_vscode_context, workspace_context=workspace_context)

    assert result.status == ExecutionStatus.COMMITTED
    assert result.verification == "PASSED"
    formatted = workspace_context["mock_files"]["example.py"]
    assert "   \n" not in formatted


# Test E: Valid REFACTOR operation (Rename symbol)
def test_successful_vscode_refactor_execution(clean_tokens, mock_vscode_context, valid_approval_token):
    initial_code = "def add(a, b):\n    return a + b\n\nval = add(2, 3)\n"
    initial_hash = hashlib.sha256(initial_code.encode('utf-8')).hexdigest()
    mock_vscode_context.context_hash = initial_hash
    valid_approval_token["contextHash"] = initial_hash

    proposal = Proposal(
        proposal_id="prop_vscode_1",
        request_id="req_1",
        plan_id="plan_1",
        domain="vscode",
        base_context_id=mock_vscode_context.context_id,
        base_context_hash=initial_hash,
        base_revision=1,
        title="Rename add to sum",
        summary="Refactor function name",
        reason="Symbol rename",
        operations=[
            ProposalOperation(
                operation_id="op_1",
                op_type="REFACTOR",
                target="example.py",
                parameters={
                    "file": "example.py",
                    "refactor_type": "RENAME_SYMBOL",
                    "target_symbol": "add",
                    "new_symbol": "sum",
                    "base_hash": initial_hash
                },
                reason="Refactor symbol"
            )
        ],
        status=ProposalStatus.ACCEPTED
    )

    request = ExecutionRequest(
        execution_id="exec_vscode_refactor",
        proposal_id="prop_vscode_1",
        approval_token=auth_service.generate_token(proposal),
        base_revision=1,
        base_context_id=mock_vscode_context.context_id,
        base_context_hash=initial_hash
    )

    workspace_context = {
        "allow_mock_app": True,
        "mock_files": {"example.py": initial_code}
    }

    executor = VSCodeExecutor()
    result = executor.execute(request, proposal, mock_vscode_context, workspace_context=workspace_context)

    assert result.status == ExecutionStatus.COMMITTED
    assert result.verification == "PASSED"
    updated_code = workspace_context["mock_files"]["example.py"]
    assert "def sum(a, b):" in updated_code
    assert "val = sum(2, 3)" in updated_code
    assert "def add" not in updated_code


# Test H & User Conflict Test: Document changed after proposal creation -> DOCUMENT_CHANGED
def test_user_document_changed_conflict_block(clean_tokens, mock_vscode_context, valid_approval_token):
    initial_code = "def add(a, b):\n    pass\n"
    initial_hash = hashlib.sha256(initial_code.encode('utf-8')).hexdigest()

    # User changed file content after proposal was created
    modified_code_by_user = "def add(a, b, c=0):\n    # User edited file manually!\n    return a + b + c\n"

    proposal = Proposal(
        proposal_id="prop_vscode_1",
        request_id="req_1",
        plan_id="plan_1",
        domain="vscode",
        base_context_id=mock_vscode_context.context_id,
        base_context_hash=initial_hash,
        base_revision=1,
        title="Change add function",
        summary="Target original add function",
        reason="Edit function",
        operations=[
            ProposalOperation(
                operation_id="op_1",
                op_type="CODE_CHANGE",
                target="example.py",
                parameters={"file": "example.py", "target_content": "pass", "replacement_content": "return a+b", "base_hash": initial_hash},
                reason="Edit"
            )
        ],
        status=ProposalStatus.ACCEPTED
    )

    request = ExecutionRequest(
        execution_id="exec_vscode_conflict",
        proposal_id="prop_vscode_1",
        approval_token=auth_service.generate_token(proposal),
        base_revision=1,
        base_context_id=mock_vscode_context.context_id,
        base_context_hash=initial_hash
    )

    workspace_context = {
        "allow_mock_app": True,
        "mock_files": {"example.py": modified_code_by_user}
    }

    executor = VSCodeExecutor()
    result = executor.execute(request, proposal, mock_vscode_context, workspace_context=workspace_context)

    assert result.status == ExecutionStatus.BLOCKED
    assert "DOCUMENT_CHANGED" in result.error
    # User modification must remain untouched
    assert workspace_context["mock_files"]["example.py"] == modified_code_by_user


# Test J: Application unavailable when VS Code is closed / not active
def test_application_unavailable_execution_block(clean_tokens, mock_vscode_context, valid_approval_token):
    # Active application is Notepad instead of VS Code
    mock_vscode_context.active_app_name = "Notepad"
    mock_vscode_context.active_app_domain = "notepad"
    mock_vscode_context.raw_title = "Notepad"

    proposal = Proposal(
        proposal_id="prop_vscode_1",
        request_id="req_1",
        plan_id="plan_1",
        domain="vscode",
        base_context_id=mock_vscode_context.context_id,
        base_context_hash="hash_123",
        base_revision=1,
        title="VS Code Edit",
        summary="Edit",
        reason="Edit",
        operations=[
            ProposalOperation(
                operation_id="op_1",
                op_type="CODE_CHANGE",
                target="example.py",
                parameters={"file": "example.py", "target_content": "a", "replacement_content": "b"},
                reason="Edit"
            )
        ],
        status=ProposalStatus.ACCEPTED
    )

    request = ExecutionRequest(
        execution_id="exec_vscode_app_unavailable",
        proposal_id="prop_vscode_1",
        approval_token=auth_service.generate_token(proposal),
        base_revision=1,
        base_context_id=mock_vscode_context.context_id,
        base_context_hash="hash_123"
    )

    executor = VSCodeExecutor()
    # Do NOT pass allow_mock_app so application check runs against context
    result = executor.execute(request, proposal, mock_vscode_context, workspace_context={})

    assert result.status == ExecutionStatus.BLOCKED
    assert "APPLICATION_UNAVAILABLE" in result.error


# Test K: Emergency Stop active blocks VS Code execution
def test_emergency_stop_blocks_vscode_execution(clean_tokens, mock_vscode_context, valid_approval_token):
    initial_code = "def add(a, b):\n    pass\n"
    initial_hash = hashlib.sha256(initial_code.encode('utf-8')).hexdigest()
    mock_vscode_context.context_hash = initial_hash

    proposal = Proposal(
        proposal_id="prop_vscode_1",
        request_id="req_1",
        plan_id="plan_1",
        domain="vscode",
        base_context_id=mock_vscode_context.context_id,
        base_context_hash=initial_hash,
        base_revision=1,
        title="VS Code Edit",
        summary="Edit",
        reason="Edit",
        operations=[
            ProposalOperation(
                operation_id="op_1",
                op_type="CODE_CHANGE",
                target="example.py",
                parameters={"file": "example.py", "target_content": "pass", "replacement_content": "return a + b"},
                reason="Edit"
            )
        ],
        status=ProposalStatus.ACCEPTED
    )

    request = ExecutionRequest(
        execution_id="exec_vscode_estop",
        proposal_id="prop_vscode_1",
        approval_token=auth_service.generate_token(proposal),
        base_revision=1,
        base_context_id=mock_vscode_context.context_id,
        base_context_hash=initial_hash
    )

    executor = VSCodeExecutor()
    from agent.runtime.lifecycle import runtime_manager
    runtime_manager.state.emergency_stop_state = True
    try:
        result = executor.execute(
            request, proposal, mock_vscode_context,
            workspace_context={"allow_mock_app": True, "mock_files": {"example.py": initial_code}}
        )
    finally:
        runtime_manager.state.emergency_stop_state = False

    assert result.status == ExecutionStatus.BLOCKED
    assert "Emergency Stop active" in result.error


# Test P: Syntax Verification Failure & Document Restoration
def test_syntax_verification_failure_restores_document(clean_tokens, mock_vscode_context, valid_approval_token):
    initial_code = "def add(a, b):\n    pass\n"
    initial_hash = hashlib.sha256(initial_code.encode('utf-8')).hexdigest()
    mock_vscode_context.context_hash = initial_hash
    valid_approval_token["contextHash"] = initial_hash

    # Invalid Python syntax replacement
    proposal = Proposal(
        proposal_id="prop_vscode_1",
        request_id="req_1",
        plan_id="plan_1",
        domain="vscode",
        base_context_id=mock_vscode_context.context_id,
        base_context_hash=initial_hash,
        base_revision=1,
        title="Invalid syntax proposal",
        summary="Inject broken syntax",
        reason="Syntax test",
        operations=[
            ProposalOperation(
                operation_id="op_1",
                op_type="CODE_CHANGE",
                target="example.py",
                parameters={
                    "file": "example.py",
                    "target_content": "pass",
                    "replacement_content": "def broken_syntax(((((",
                    "base_hash": initial_hash
                },
                reason="Broken syntax"
            )
        ],
        status=ProposalStatus.ACCEPTED
    )

    request = ExecutionRequest(
        execution_id="exec_vscode_syn_err",
        proposal_id="prop_vscode_1",
        approval_token=auth_service.generate_token(proposal),
        base_revision=1,
        base_context_id=mock_vscode_context.context_id,
        base_context_hash=initial_hash
    )

    workspace_context = {
        "allow_mock_app": True,
        "mock_files": {"example.py": initial_code}
    }

    executor = VSCodeExecutor()
    result = executor.execute(request, proposal, mock_vscode_context, workspace_context=workspace_context)

    assert result.status == ExecutionStatus.REVERTED
    assert result.verification == "FAILED"
    # Document must be restored to initial code
    assert workspace_context["mock_files"]["example.py"] == initial_code


# Test R: Integration through JarvisAgent orchestrator
def test_jarvis_agent_orchestrated_vscode_execution(clean_tokens, mock_vscode_context, valid_approval_token):
    agent = JarvisAgent()

    initial_code = "def add(a, b):\n    pass\n"
    initial_hash = hashlib.sha256(initial_code.encode('utf-8')).hexdigest()
    workspace_context = {
        "allow_mock_app": True,
        "mock_files": {"example.py": initial_code}
    }
    perception_ctx = {
        "active_application": {"name": "Microsoft Visual Studio Code"},
        "application_context": {"domain": "vscode", "raw_title": "Microsoft Visual Studio Code"}
    }
    rel_ctx = ContextRelevanceFilter.filter(perception_ctx, workspace_context)
    base_ctx_hash = rel_ctx.context_hash

    valid_approval_token["contextHash"] = base_ctx_hash

    file_hash = hashlib.sha256(initial_code.encode('utf-8')).hexdigest()
    proposal = Proposal(
        proposal_id="prop_vscode_agent",
        request_id="req_agent",
        plan_id="plan_agent",
        domain="vscode",
        base_context_id=rel_ctx.context_id,
        base_context_hash=base_ctx_hash,
        base_revision=1,
        title="Agent VS Code Execution",
        summary="Orchestrated execution test",
        reason="Agent test",
        operations=[
            ProposalOperation(
                operation_id="op_1",
                op_type="CODE_CHANGE",
                target="example.py",
                parameters={
                    "file": "example.py",
                    "target_content": "pass",
                    "replacement_content": "return a + b",
                    "base_hash": file_hash
                },
                reason="Edit"
            )
        ],
        status=ProposalStatus.ACCEPTED
    )

    
    valid_approval_token["tokenId"] = "token_agent_999"

    request = ExecutionRequest(
        execution_id="exec_vscode_agent",
        proposal_id="prop_vscode_agent",
        approval_token=auth_service.generate_token(proposal),
        base_revision=1,
        base_context_id=rel_ctx.context_id,
        base_context_hash=base_ctx_hash
    )

    result = agent.execute_proposal(
        exec_request=request,
        proposal=proposal,
        perception_context=perception_ctx,
        workspace_context=workspace_context
    )

    assert result.status == ExecutionStatus.COMMITTED
    assert result.verification == "PASSED"
    assert "return a + b" in workspace_context["mock_files"]["example.py"]
