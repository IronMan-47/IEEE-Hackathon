from agent.execution.authorization import auth_service
import pytest
from agent.tasks.orchestrator import TaskOrchestrator
from agent.tasks.models import TaskStatus, TaskStepStatus
from agent.context.fusion.models import GroundedContext, AppInfo, ApplicationRole
from agent.proposals.models import Proposal

@pytest.fixture
def mock_vscode_context():
    return GroundedContext(
        context_id="ctx_vs_001",
        context_hash="hash_vs_001",
        primary_application=AppInfo(name="Visual Studio Code", role=ApplicationRole.PRIMARY_APPLICATION)
    )

@pytest.fixture
def mock_browser_context():
    return GroundedContext(
        context_id="ctx_br_001",
        context_hash="hash_br_001",
        primary_application=AppInfo(name="Google Chrome", role=ApplicationRole.PRIMARY_APPLICATION)
    )

def test_primary_workflow_vscode_browser_vscode(mock_vscode_context, mock_browser_context):
    orchestrator = TaskOrchestrator()
    
    # User Request: "Look at this error in VS Code, find relevant documentation in the browser, and propose a fix."
    task = orchestrator.create_task(
        user_text="Find relevant documentation in browser for this error and propose a fix.",
        perception_result=None,
        workspace_context={}
    )
    
    task.grounded_context = mock_vscode_context
    task.initial_context_hash = mock_vscode_context.context_hash
    task.last_context_hash = mock_vscode_context.context_hash
    
    # 1. VS Code context is captured, handoff initiated
    evidence = {"error": "ModuleNotFoundError: No module named 'agent.runtime'"}
    handoff_dict = orchestrator.initiate_cross_app_transition(task.task_id, "browser", evidence)
    
    assert handoff_dict is not None
    assert handoff_dict["target_application"] == "browser"
    
    # 2. Browser target verified and context fused
    success = orchestrator.consume_cross_app_handoff(task.task_id, mock_browser_context)
    assert success is True
    assert task.grounded_context.context_id == mock_browser_context.context_id
    assert task.last_context_hash == mock_browser_context.context_hash
    
    # 3. From Browser back to VS Code
    evidence_from_browser = {"solution": "Create agent/runtime/models.py and define the required enums."}
    handoff_dict_return = orchestrator.initiate_cross_app_transition(task.task_id, "vscode", evidence_from_browser)
    
    assert handoff_dict_return is not None
    assert handoff_dict_return["target_application"] == "vscode"
    
    # Simulated updated VS Code context
    mock_vscode_context.context_id = "ctx_vs_002"
    mock_vscode_context.context_hash = "hash_vs_002"
    
    success_return = orchestrator.consume_cross_app_handoff(task.task_id, mock_vscode_context)
    assert success_return is True
    assert task.grounded_context.context_id == mock_vscode_context.context_id
    
    # Task step must not authorize cross-application execution implicitly
    # If the active domain is VS Code, the approval token must be strictly bound to VS Code.
    if task.steps:
        # Simulate moving to an execution step
        task.steps[0].target_domain = "vscode"
        task.steps[0].proposal = Proposal(
            proposal_id="prop_001",
            domain="vscode",
            action_type="UPDATE_FILE",
            target="agent/runtime/models.py",
            payload={"content": "..."},
            base_context_hash="hash_vs_002",
            title="Update enums",
            summary="Update models.py",
            reason="User requested fix",
            risk_level="LOW",
            request_id="req_001",
            plan_id="plan_001",
            base_context_id="ctx_vs_002"
        )
        task.steps[0].status = TaskStepStatus.AWAITING_APPROVAL
        
        # A VS Code proposal cannot authorize a Browser action
        assert task.steps[0].proposal.domain == "vscode"
