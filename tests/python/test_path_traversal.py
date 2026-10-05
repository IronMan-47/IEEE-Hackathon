import pytest
from agent.execution.models import ExecutionRequest
from agent.proposals.models import Proposal, ProposalOperation
from agent.execution.authorization import auth_service
from agent.execution.vscode_executor import VSCodeExecutor
from agent.context.relevance_filter import RelevantContext
import hashlib

def test_path_traversal_blocked():
    initial_code = "def add(a, b):\n    pass\n"
    initial_hash = hashlib.sha256(initial_code.encode('utf-8')).hexdigest()

    mock_vscode_context = RelevantContext(
        context_id="ctx_1",
        context_hash="hash_1",
        active_app_domain="vscode",
        active_app_name="Visual Studio Code",
        active_file="example.py",
        extracted_fields={"content": initial_code}
    )

    proposal = Proposal(
        proposal_id="prop_vscode_1",
        request_id="req_1",
        plan_id="plan_1",
        domain="vscode",
        base_context_id=mock_vscode_context.context_id,
        base_context_hash=initial_hash,
        base_revision=1,
        title="Malicious Edit",
        summary="Edit",
        reason="Edit",
        operations=[
            ProposalOperation(
                operation_id="op_1",
                op_type="CODE_CHANGE",
                target="../../../Windows/System32/config/SAM",
                reason="malicious",
                parameters={"base_hash": initial_hash}
            )
        ]
    )

    request = ExecutionRequest(
        execution_id="exec_vscode_1",
        proposal_id="prop_vscode_1",
        approval_token=auth_service.generate_token(proposal),
        base_revision=1,
        base_context_id=mock_vscode_context.context_id,
        base_context_hash=initial_hash
    )

    executor = VSCodeExecutor()
    result = executor.execute(request, proposal, mock_vscode_context, workspace_context={})

    assert result.status.value == "BLOCKED"
    assert "PATH_TRAVERSAL_REJECTED" in result.error
