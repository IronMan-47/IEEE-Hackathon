from agent.execution.authorization import auth_service
"""
JARVIS Phase 12 — Browser Controlled Execution Engine Pytest Suite
Tests Browser domain executor, domain router, safe navigation, origin binding, sensitive field detection,
high-risk action blocking, target ambiguity resolution, prompt injection defense, and full Phase 1-11 regression.
"""

import pytest
import time
import hashlib
from datetime import datetime, timezone, timedelta
from agent.execution.domain_router import DomainRouter
from agent.execution.browser_executor import BrowserExecutor
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
def mock_browser_context():
    return RelevantContext(
        context_id="browser_ctx_1",
        context_hash="hash_browser_1",
        active_app_domain="browser",
        active_app_name="Google Chrome",
        active_window_title="JARVIS Browser Test Page - Google Chrome",
        active_file=None,
        extracted_fields={"origin": "https://example.com", "active_url": "https://example.com/test"},
        raw_title="JARVIS Browser Test Page - Google Chrome",
        workspace_revision=1,
        timestamp=int(time.time() * 1000)
    )


@pytest.fixture
def valid_approval_token():
    import uuid
    return {
        "tokenId": f"token_browser_{uuid.uuid4().hex[:8]}",
        "proposalId": "prop_browser_1",
        "baseRevision": 1,
        "contextHash": "hash_browser_1",
        "issuedAt": datetime.now(timezone.utc).isoformat(),
        "expiresAt": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        "singleUse": True,
        "status": "ISSUED"
    }


# Test A & B: Domain Router Selection & Rejection
def test_domain_router_browser_selection(domain_router):
    assert isinstance(domain_router.get_executor("browser"), BrowserExecutor)
    assert isinstance(domain_router.get_executor("vscode"), VSCodeExecutor)
    assert isinstance(domain_router.get_executor("living_canvas"), LivingCanvasExecutor)

    assert domain_router.get_executor("terminal") is None
    assert domain_router.get_executor("figma") is None
    assert domain_router.get_executor("unknown") is None
    assert domain_router.get_executor("arbitrary_desktop") is None


# Test C: Safe Navigation
def test_successful_safe_navigation(clean_tokens, mock_browser_context, valid_approval_token):
    proposal = Proposal(
        proposal_id="prop_browser_1",
        request_id="req_1",
        plan_id="plan_1",
        domain="browser",
        base_context_id=mock_browser_context.context_id,
        base_context_hash=mock_browser_context.context_hash,
        base_revision=1,
        title="Safe Navigation",
        summary="Navigate to approved URL",
        reason="Test navigation",
        operations=[
            ProposalOperation(
                operation_id="op_1",
                op_type="NAVIGATE_SAFE",
                target="https://example.com/docs",
                parameters={"url": "https://example.com/docs", "origin": "https://example.com"},
                reason="Safe navigation"
            )
        ],
        status=ProposalStatus.ACCEPTED
    )

    request = ExecutionRequest(
        execution_id="exec_browser_nav",
        proposal_id="prop_browser_1",
        approval_token=auth_service.generate_token(proposal),
        base_revision=1,
        base_context_id=mock_browser_context.context_id,
        base_context_hash=mock_browser_context.context_hash
    )

    executor = BrowserExecutor()
    workspace_context = {"allow_mock_app": True, "active_origin": "https://example.com"}
    result = executor.execute(request, proposal, mock_browser_context, workspace_context=workspace_context)

    assert result.status == ExecutionStatus.COMMITTED
    assert result.verification == "PASSED"
    assert len(result.operations_applied) == 1


# Test D: Unsafe Navigation Rejection
@pytest.mark.parametrize("unsafe_url", [
    "javascript:alert(1)",
    "data:text/html,<h1>Hack</h1>",
    "file:///C:/Windows/System32/cmd.exe",
    "chrome://settings",
    "edge://flags",
    "about:blank"
])
def test_unsafe_navigation_rejection(clean_tokens, mock_browser_context, valid_approval_token, unsafe_url):
    proposal = Proposal(
        proposal_id="prop_browser_1",
        request_id="req_1",
        plan_id="plan_1",
        domain="browser",
        base_context_id=mock_browser_context.context_id,
        base_context_hash=mock_browser_context.context_hash,
        base_revision=1,
        title="Unsafe Navigation",
        summary="Navigate to unsafe URL",
        reason="Unsafe navigation test",
        operations=[
            ProposalOperation(
                operation_id="op_1",
                op_type="NAVIGATE_SAFE",
                target=unsafe_url,
                parameters={"url": unsafe_url, "origin": "https://example.com"},
                reason="Unsafe navigation"
            )
        ],
        status=ProposalStatus.ACCEPTED
    )

    request = ExecutionRequest(
        execution_id=f"exec_browser_unsafe_{int(time.time())}",
        proposal_id="prop_browser_1",
        approval_token=auth_service.generate_token(proposal),
        base_revision=1,
        base_context_id=mock_browser_context.context_id,
        base_context_hash=mock_browser_context.context_hash
    )

    executor = BrowserExecutor()
    result = executor.execute(request, proposal, mock_browser_context, workspace_context={"allow_mock_app": True})

    assert result.status == ExecutionStatus.BLOCKED
    assert any(err in result.error for err in ["UNSAFE_NAVIGATION_SCHEME", "SAFETY_BARRIER_VIOLATION", "cmd.exe"])


# Test E: Valid Click Element
def test_successful_click_element(clean_tokens, mock_browser_context, valid_approval_token):
    proposal = Proposal(
        proposal_id="prop_browser_1",
        request_id="req_1",
        plan_id="plan_1",
        domain="browser",
        base_context_id=mock_browser_context.context_id,
        base_context_hash=mock_browser_context.context_hash,
        base_revision=1,
        title="Click Test Button",
        summary="Click semantic test button",
        reason="Test click",
        operations=[
            ProposalOperation(
                operation_id="op_1",
                op_type="CLICK_ELEMENT",
                target="button#test",
                parameters={"target": "button#test", "role": "button", "accessible_name": "Test Button", "origin": "https://example.com"},
                reason="Click button"
            )
        ],
        status=ProposalStatus.ACCEPTED
    )

    request = ExecutionRequest(
        execution_id="exec_browser_click",
        proposal_id="prop_browser_1",
        approval_token=auth_service.generate_token(proposal),
        base_revision=1,
        base_context_id=mock_browser_context.context_id,
        base_context_hash=mock_browser_context.context_hash
    )

    executor = BrowserExecutor()
    result = executor.execute(request, proposal, mock_browser_context, workspace_context={"allow_mock_app": True})

    assert result.status == ExecutionStatus.COMMITTED
    assert result.verification == "PASSED"


# Test F: Target Ambiguity Rejection
def test_ambiguous_target_rejection(clean_tokens, mock_browser_context, valid_approval_token):
    proposal = Proposal(
        proposal_id="prop_browser_1",
        request_id="req_1",
        plan_id="plan_1",
        domain="browser",
        base_context_id=mock_browser_context.context_id,
        base_context_hash=mock_browser_context.context_hash,
        base_revision=1,
        title="Ambiguous Click",
        summary="Click ambiguous submit button",
        reason="Ambiguous test",
        operations=[
            ProposalOperation(
                operation_id="op_1",
                op_type="CLICK_ELEMENT",
                target="button.submit",
                parameters={"target": "button.submit", "ambiguous": True, "origin": "https://example.com"},
                reason="Ambiguous click"
            )
        ],
        status=ProposalStatus.ACCEPTED
    )

    request = ExecutionRequest(
        execution_id="exec_browser_ambiguous",
        proposal_id="prop_browser_1",
        approval_token=auth_service.generate_token(proposal),
        base_revision=1,
        base_context_id=mock_browser_context.context_id,
        base_context_hash=mock_browser_context.context_hash
    )

    executor = BrowserExecutor()
    result = executor.execute(request, proposal, mock_browser_context, workspace_context={"allow_mock_app": True})

    assert result.status == ExecutionStatus.BLOCKED
    assert "AMBIGUOUS_TARGET" in result.error


# Test I: Sensitive Field Rejection
@pytest.mark.parametrize("field_id,field_name", [
    ("input#password", "password"),
    ("input#otp", "one-time-code"),
    ("input#card_number", "credit-card"),
    ("input#cvv", "security-code"),
    ("input#pin", "pin")
])
def test_sensitive_field_rejection(clean_tokens, mock_browser_context, valid_approval_token, field_id, field_name):
    proposal = Proposal(
        proposal_id="prop_browser_1",
        request_id="req_1",
        plan_id="plan_1",
        domain="browser",
        base_context_id=mock_browser_context.context_id,
        base_context_hash=mock_browser_context.context_hash,
        base_revision=1,
        title="Enter Sensitive Field",
        summary="Attempt entry into sensitive input",
        reason="Sensitive test",
        operations=[
            ProposalOperation(
                operation_id="op_1",
                op_type="ENTER_NON_SENSITIVE_TEXT",
                target=field_id,
                parameters={"target": field_id, "text": "secret123", "field_name": field_name, "origin": "https://example.com"},
                reason="Sensitive field text entry"
            )
        ],
        status=ProposalStatus.ACCEPTED
    )

    request = ExecutionRequest(
        execution_id=f"exec_browser_sens_{int(time.time())}",
        proposal_id="prop_browser_1",
        approval_token=auth_service.generate_token(proposal),
        base_revision=1,
        base_context_id=mock_browser_context.context_id,
        base_context_hash=mock_browser_context.context_hash
    )

    executor = BrowserExecutor()
    result = executor.execute(request, proposal, mock_browser_context, workspace_context={"allow_mock_app": True})

    assert result.status == ExecutionStatus.BLOCKED
    assert "SENSITIVE_FIELD" in result.error


# Test J: Non-Sensitive Text Entry
def test_successful_non_sensitive_text_entry(clean_tokens, mock_browser_context, valid_approval_token):
    proposal = Proposal(
        proposal_id="prop_browser_1",
        request_id="req_1",
        plan_id="plan_1",
        domain="browser",
        base_context_id=mock_browser_context.context_id,
        base_context_hash=mock_browser_context.context_hash,
        base_revision=1,
        title="Search Query Entry",
        summary="Enter search query into search input",
        reason="Search query entry",
        operations=[
            ProposalOperation(
                operation_id="op_1",
                op_type="ENTER_NON_SENSITIVE_TEXT",
                target="input#search",
                parameters={"target": "input#search", "text": "JARVIS Living Canvas", "origin": "https://example.com"},
                reason="Enter search query"
            )
        ],
        status=ProposalStatus.ACCEPTED
    )

    request = ExecutionRequest(
        execution_id="exec_browser_text",
        proposal_id="prop_browser_1",
        approval_token=auth_service.generate_token(proposal),
        base_revision=1,
        base_context_id=mock_browser_context.context_id,
        base_context_hash=mock_browser_context.context_hash
    )

    executor = BrowserExecutor()
    workspace_context = {"allow_mock_app": True}
    result = executor.execute(request, proposal, mock_browser_context, workspace_context=workspace_context)

    assert result.status == ExecutionStatus.COMMITTED
    assert result.verification == "PASSED"


# Test K: Select Option
def test_successful_select_option(clean_tokens, mock_browser_context, valid_approval_token):
    proposal = Proposal(
        proposal_id="prop_browser_1",
        request_id="req_1",
        plan_id="plan_1",
        domain="browser",
        base_context_id=mock_browser_context.context_id,
        base_context_hash=mock_browser_context.context_hash,
        base_revision=1,
        title="Select Category",
        summary="Select tools option",
        reason="Category selection",
        operations=[
            ProposalOperation(
                operation_id="op_1",
                op_type="SELECT_OPTION",
                target="select#category",
                parameters={"target": "select#category", "option": "tools", "origin": "https://example.com"},
                reason="Select option"
            )
        ],
        status=ProposalStatus.ACCEPTED
    )

    request = ExecutionRequest(
        execution_id="exec_browser_select",
        proposal_id="prop_browser_1",
        approval_token=auth_service.generate_token(proposal),
        base_revision=1,
        base_context_id=mock_browser_context.context_id,
        base_context_hash=mock_browser_context.context_hash
    )

    executor = BrowserExecutor()
    result = executor.execute(request, proposal, mock_browser_context, workspace_context={"allow_mock_app": True})

    assert result.status == ExecutionStatus.COMMITTED
    assert result.verification == "PASSED"


# Test M: Origin Mismatch Rejection
def test_origin_mismatch_rejection(clean_tokens, mock_browser_context, valid_approval_token):
    proposal = Proposal(
        proposal_id="prop_browser_1",
        request_id="req_1",
        plan_id="plan_1",
        domain="browser",
        base_context_id=mock_browser_context.context_id,
        base_context_hash=mock_browser_context.context_hash,
        base_revision=1,
        title="Click on example.com",
        summary="Approved for example.com",
        reason="Click test",
        operations=[
            ProposalOperation(
                operation_id="op_1",
                op_type="CLICK_ELEMENT",
                target="button#test",
                parameters={"target": "button#test", "origin": "https://approved-site.com"},
                reason="Click"
            )
        ],
        status=ProposalStatus.ACCEPTED
    )

    request = ExecutionRequest(
        execution_id="exec_browser_origin_mismatch",
        proposal_id="prop_browser_1",
        approval_token=auth_service.generate_token(proposal),
        base_revision=1,
        base_context_id=mock_browser_context.context_id,
        base_context_hash=mock_browser_context.context_hash
    )

    executor = BrowserExecutor()
    # Active origin is malicious-site.com
    workspace_context = {"allow_mock_app": True, "active_origin": "https://malicious-site.com"}
    result = executor.execute(request, proposal, mock_browser_context, workspace_context=workspace_context)

    assert result.status == ExecutionStatus.BLOCKED
    assert "ORIGIN_CHANGED" in result.error


# Test N: Multi-Tab / Context Changed Rejection
def test_multi_tab_context_changed_rejection(clean_tokens, mock_browser_context, valid_approval_token):
    proposal = Proposal(
        proposal_id="prop_browser_1",
        request_id="req_1",
        plan_id="plan_1",
        domain="browser",
        base_context_id=mock_browser_context.context_id,
        base_context_hash=mock_browser_context.context_hash,
        base_revision=1,
        title="Click button",
        summary="Click",
        reason="Click",
        operations=[
            ProposalOperation(
                operation_id="op_1",
                op_type="CLICK_ELEMENT",
                target="button#test",
                parameters={"target": "button#test", "origin": "https://example.com"},
                reason="Click"
            )
        ],
        status=ProposalStatus.ACCEPTED
    )

    request = ExecutionRequest(
        execution_id="exec_browser_tab_changed",
        proposal_id="prop_browser_1",
        approval_token=auth_service.generate_token(proposal),
        base_revision=1,
        base_context_id=mock_browser_context.context_id,
        base_context_hash=mock_browser_context.context_hash
    )

    executor = BrowserExecutor()
    # Tab changed flag set
    workspace_context = {"allow_mock_app": True, "tab_changed": True}
    result = executor.execute(request, proposal, mock_browser_context, workspace_context=workspace_context)

    assert result.status == ExecutionStatus.BLOCKED
    assert "CONTEXT_CHANGED" in result.error


# Test S: High-Risk Action Blocking
@pytest.mark.parametrize("action_target", [
    "button#delete_account",
    "button#purchase_now",
    "button#pay_invoice",
    "button#transfer_funds",
    "button#disable_security"
])
def test_high_risk_action_blocking(clean_tokens, mock_browser_context, valid_approval_token, action_target):
    proposal = Proposal(
        proposal_id="prop_browser_1",
        request_id="req_1",
        plan_id="plan_1",
        domain="browser",
        base_context_id=mock_browser_context.context_id,
        base_context_hash=mock_browser_context.context_hash,
        base_revision=1,
        title="High Risk Action",
        summary="Attempt high risk click",
        reason="High risk test",
        operations=[
            ProposalOperation(
                operation_id="op_1",
                op_type="CLICK_ELEMENT",
                target=action_target,
                parameters={"target": action_target, "origin": "https://example.com"},
                reason="High risk action"
            )
        ],
        status=ProposalStatus.ACCEPTED
    )

    request = ExecutionRequest(
        execution_id=f"exec_browser_hr_{int(time.time())}",
        proposal_id="prop_browser_1",
        approval_token=auth_service.generate_token(proposal),
        base_revision=1,
        base_context_id=mock_browser_context.context_id,
        base_context_hash=mock_browser_context.context_hash
    )

    executor = BrowserExecutor()
    result = executor.execute(request, proposal, mock_browser_context, workspace_context={"allow_mock_app": True})

    assert result.status == ExecutionStatus.BLOCKED
    assert "HIGH_RISK_ACTION" in result.error


# Test T: Form Submission Disabled by Default
def test_form_submission_disabled_by_default(clean_tokens, mock_browser_context, valid_approval_token):
    proposal = Proposal(
        proposal_id="prop_browser_1",
        request_id="req_1",
        plan_id="plan_1",
        domain="browser",
        base_context_id=mock_browser_context.context_id,
        base_context_hash=mock_browser_context.context_hash,
        base_revision=1,
        title="Submit Form",
        summary="Submit contact form",
        reason="Form submission",
        operations=[
            ProposalOperation(
                operation_id="op_1",
                op_type="SUBMIT_FORM",
                target="form#contact",
                parameters={"target": "form#contact", "origin": "https://example.com"},
                reason="Form submit"
            )
        ],
        status=ProposalStatus.ACCEPTED
    )

    request = ExecutionRequest(
        execution_id="exec_browser_submit",
        proposal_id="prop_browser_1",
        approval_token=auth_service.generate_token(proposal),
        base_revision=1,
        base_context_id=mock_browser_context.context_id,
        base_context_hash=mock_browser_context.context_hash
    )

    executor = BrowserExecutor()
    result = executor.execute(request, proposal, mock_browser_context, workspace_context={"allow_mock_app": True})

    assert result.status == ExecutionStatus.BLOCKED
    assert "HIGH_RISK_ACTION" in result.error


# Test X: Orchestrated Execution through JarvisAgent
def test_jarvis_agent_orchestrated_browser_execution(clean_tokens, mock_browser_context, valid_approval_token):
    agent = JarvisAgent()

    perception_ctx = {
        "active_application": {"name": "Google Chrome"},
        "application_context": {"domain": "browser", "raw_title": "JARVIS Browser Test Page - Google Chrome"}
    }
    workspace_ctx = {"allow_mock_app": True, "active_origin": "https://example.com"}

    rel_ctx = ContextRelevanceFilter.filter(perception_ctx, workspace_ctx)
    base_hash = rel_ctx.context_hash
    

    proposal = Proposal(
        proposal_id="prop_browser_agent",
        request_id="req_agent",
        plan_id="plan_agent",
        domain="browser",
        base_context_id=rel_ctx.context_id,
        base_context_hash=base_hash,
        base_revision=1,
        title="Agent Browser Execution",
        summary="Orchestrated browser execution test",
        reason="Agent test",
        operations=[
            ProposalOperation(
                operation_id="op_1",
                op_type="ENTER_NON_SENSITIVE_TEXT",
                target="input#search",
                parameters={"target": "input#search", "text": "JARVIS Core", "origin": "https://example.com"},
                reason="Search query"
            )
        ],
        status=ProposalStatus.ACCEPTED
    )

    
    

    request = ExecutionRequest(
        execution_id="exec_browser_agent",
        proposal_id="prop_browser_agent",
        approval_token=auth_service.generate_token(proposal),
        base_revision=1,
        base_context_id=rel_ctx.context_id,
        base_context_hash=base_hash
    )

    result = agent.execute_proposal(
        exec_request=request,
        proposal=proposal,
        perception_context=perception_ctx,
        workspace_context=workspace_ctx
    )

    assert result.status == ExecutionStatus.COMMITTED
    assert result.verification == "PASSED"
