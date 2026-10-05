"""
JARVIS Python Agent Core — Phase 12 Browser Domain Executor
Implements controlled, typed browser-native actions (NAVIGATE_SAFE, CLICK_ELEMENT,
ENTER_NON_SENSITIVE_TEXT, SELECT_OPTION, SCROLL_TO_ELEMENT) with origin binding,
sensitive field detection, high-risk action blocking, and independent verification.
"""

import urllib.parse
import uuid
from datetime import datetime, timezone
from typing import Tuple, Optional, Dict, Any, List, Set
from agent.execution.base import BaseDomainExecutor
from agent.execution.models import ExecutionRequest, ExecutionStatus, ExecutionResult
from agent.execution.safety_barrier import ExecutionSafetyBarrier
from agent.proposals.models import Proposal
from agent.context.relevance_filter import RelevantContext
from agent.core.logging import logger

from agent.core.operations import BROWSER_OPS as ALLOWED_BROWSER_OPS

UNSAFE_URL_SCHEMES = {"javascript:", "data:", "file:", "chrome:", "edge:", "about:", "opera:", "view-source:"}

SENSITIVE_FIELD_KEYWORDS = {
    "password", "current-password", "new-password", "one-time-code", "otp",
    "cvv", "card-number", "credit-card", "debit-card", "security-code", "pin", "ssn"
}

HIGH_RISK_ACTION_KEYWORDS = {
    "delete account", "delete permanently", "purchase", "buy now", "pay",
    "transfer", "send money", "confirm payment", "change password",
    "disable security", "grant access", "revoke access"
}


class BrowserExecutor(BaseDomainExecutor):
    def can_execute(self, domain: str) -> bool:
        return (domain or "").lower().strip() == "browser"

    def execute(
        self,
        request: ExecutionRequest,
        proposal: Proposal,
        context: RelevantContext,
        workspace_context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        logger.info(f"AUDIT EVENT [BROWSER_EXECUTION_REQUESTED] ID [{request.execution_id}]: Proposal [{proposal.proposal_id}]")
        logger.warning(f"AUDIT EVENT [BROWSER_EXECUTION_SIMULATED] ID [{request.execution_id}]: Browser execution is purely SIMULATED in memory. No actual browser control occurs.")

        # 1. Domain Check
        if not self.can_execute(proposal.domain):
            return self._build_blocked_result(
                request,
                f"UNSUPPORTED_DOMAIN: BrowserExecutor cannot handle domain '{proposal.domain}'"
            )

        # 2. Application Availability & Browser Process Check
        app_name = (context.active_app_name or context.active_app_domain or "").lower()
        title = (context.raw_title or context.active_window_title or "").lower()
        is_browser = any(b in app_name or b in title for b in ["chrome", "edge", "firefox", "brave", "opera", "browser"])

        if not is_browser:
            logger.warn(f"AUDIT EVENT [BROWSER_EXECUTION_BLOCKED] ID [{request.execution_id}]: Application '{app_name}' is not a Browser")
            return self._build_blocked_result(
                request,
                f"APPLICATION_UNAVAILABLE: Browser is not active. Current app: '{context.active_app_name}'. JARVIS will not start applications automatically."
            )

        # 3. Origin & Page Context Revalidation
        active_origin = self._extract_active_origin(context, workspace_context)
        approved_origin = self._extract_approved_origin(proposal)

        if approved_origin and active_origin and approved_origin.lower() != active_origin.lower():
            logger.warn(f"AUDIT EVENT [BROWSER_ORIGIN_BLOCKED] ID [{request.execution_id}]: Active origin '{active_origin}' != Approved origin '{approved_origin}'")
            return self._build_blocked_result(
                request,
                f"ORIGIN_CHANGED: Current origin '{active_origin}' does not match approved proposal origin '{approved_origin}'."
            )

        # Tab / Page Context check
        if workspace_context and workspace_context.get("tab_changed"):
            logger.warn(f"AUDIT EVENT [BROWSER_TAB_BLOCKED] ID [{request.execution_id}]: Active tab changed")
            return self._build_blocked_result(request, "CONTEXT_CHANGED: Active browser page or tab context changed.")

        # 4. Global Pre-Execution Safety Barrier Validation
        valid, err_reason, barrier_result = ExecutionSafetyBarrier.validate_execution_request(
            request=request,
            proposal=proposal,
            context=context,
            workspace_revision=proposal.base_revision
        )
        if not valid and barrier_result:
            return barrier_result

        # 5. Single-Use Token Consumption (Prevent Replay Attacks)
        token_id = request.approval_token.get("token_id", "")
        if not ExecutionSafetyBarrier.consume_token_atomically(token_id):
            return self._build_blocked_result(request, f"TOKEN_REPLAY_ATTACK_PREVENTED: ApprovalToken [{token_id}] was already consumed.")

        logger.info(f"AUDIT EVENT [BROWSER_CONTEXT_VALIDATED] ID [{request.execution_id}]: Origin [{active_origin or 'local'}] validated")

        # 6. Apply Controlled Browser Operations
        operations_applied = []
        browser_state = self._get_browser_state(workspace_context)

        for op in proposal.operations:
            op_type = op.op_type.upper()
            if op_type not in ALLOWED_BROWSER_OPS:
                return self._build_blocked_result(request, f"UNSUPPORTED_OPERATION: Browser operation '{op_type}' is not permitted.")

            # A. Safe Navigation
            if op_type == "NAVIGATE_SAFE":
                dest_url = op.parameters.get("url") or op.target
                if not dest_url:
                    return self._build_blocked_result(request, "INVALID_NAVIGATION: Missing destination URL.")

                dest_url_lower = dest_url.lower().strip()
                if any(dest_url_lower.startswith(scheme) for scheme in UNSAFE_URL_SCHEMES):
                    logger.error(f"AUDIT EVENT [BROWSER_SAFETY_VIOLATION] ID [{request.execution_id}]: Unsafe scheme in '{dest_url}'")
                    return self._build_blocked_result(request, f"UNSAFE_NAVIGATION_SCHEME: Navigation scheme in '{dest_url}' is strictly prohibited.")

                parsed = urllib.parse.urlparse(dest_url)
                if parsed.scheme not in ["https", "http"]:
                    return self._build_blocked_result(request, f"UNSAFE_NAVIGATION_SCHEME: Only http/https schemes allowed. URL: {dest_url}")

                browser_state["url"] = dest_url
                browser_state["origin"] = f"{parsed.scheme}://{parsed.netloc}"
                operations_applied.append(op.model_dump() if hasattr(op, "model_dump") else dict(op))

            # B. Click Element
            elif op_type == "CLICK_ELEMENT":
                target = op.target or op.parameters.get("target") or ""
                params = op.parameters or {}

                # Reject raw coordinates (x, y)
                if "x" in params or "y" in params or "coordinate" in params:
                    return self._build_blocked_result(request, "UNSUPPORTED_TARGETING: Raw screen coordinates (x, y) are strictly prohibited.")

                el_info = browser_state.get("elements", {}).get(target, {})

                # High-Risk Action Check (evaluated before DOM lookup)
                action_text = (target + " " + target.replace("_", " ") + " " + str(params) + " " + el_info.get("text", "")).lower()
                for keyword in HIGH_RISK_ACTION_KEYWORDS:
                    if keyword in action_text:
                        logger.warn(f"AUDIT EVENT [BROWSER_HIGH_RISK_BLOCKED] ID [{request.execution_id}]: Keyword '{keyword}' detected")
                        return self._build_blocked_result(request, f"HIGH_RISK_ACTION: Action on '{target}' involves high-risk operation ('{keyword}'). Executing blocked.")

                # Target ambiguity check
                if params.get("ambiguous") or browser_state.get("ambiguous_targets", {}).get(target):
                    logger.warn(f"AUDIT EVENT [BROWSER_TARGET_AMBIGUOUS] ID [{request.execution_id}]: Target '{target}' is ambiguous")
                    return self._build_blocked_result(request, f"AMBIGUOUS_TARGET: Multiple matching elements found for target '{target}'. User resolution required.")

                # Target missing check
                if params.get("missing") or target not in browser_state.get("elements", {}):
                    return self._build_blocked_result(request, f"TARGET_NOT_FOUND: Target element '{target}' not found on active page.")

                # Target disabled check
                if el_info.get("disabled"):
                    return self._build_blocked_result(request, f"TARGET_DISABLED: Target element '{target}' is disabled.")

                el_info["clicked"] = True
                operations_applied.append(op.model_dump() if hasattr(op, "model_dump") else dict(op))

            # C. Enter Non-Sensitive Text
            elif op_type == "ENTER_NON_SENSITIVE_TEXT":
                target = op.target or op.parameters.get("target") or ""
                params = op.parameters or {}
                input_text = params.get("text") or params.get("value") or ""

                el_info = browser_state.get("elements", {}).get(target, {})
                field_attributes = (target + " " + str(params) + " " + str(el_info)).lower()

                # Sensitive Field Detection
                for kw in SENSITIVE_FIELD_KEYWORDS:
                    if kw in field_attributes:
                        logger.error(f"AUDIT EVENT [BROWSER_SENSITIVE_FIELD_BLOCKED] ID [{request.execution_id}]: Sensitive keyword '{kw}' detected")
                        return self._build_blocked_result(request, f"SENSITIVE_FIELD: Text entry into sensitive field '{target}' (keyword: '{kw}') is strictly prohibited.")

                # Target missing check
                if params.get("missing") or target not in browser_state.get("elements", {}):
                    return self._build_blocked_result(request, f"TARGET_NOT_FOUND: Target element '{target}' not found on active page.")

                el_info["value"] = input_text
                operations_applied.append(op.model_dump() if hasattr(op, "model_dump") else dict(op))

            # D. Select Option
            elif op_type == "SELECT_OPTION":
                target = op.target or op.parameters.get("target") or ""
                params = op.parameters or {}
                option_val = params.get("option") or params.get("value") or ""

                el_info = browser_state.get("elements", {}).get(target, {})
                available_options = el_info.get("options", [])
                if available_options and option_val not in available_options:
                    return self._build_blocked_result(request, f"OPTION_NOT_FOUND: Requested option '{option_val}' does not exist in target select '{target}'.")

                el_info["selected"] = option_val
                operations_applied.append(op.model_dump() if hasattr(op, "model_dump") else dict(op))

            # E. Scroll To Element
            elif op_type == "SCROLL_TO_ELEMENT":
                target = op.target or op.parameters.get("target") or ""
                el_info = browser_state.get("elements", {}).get(target, {})
                el_info["scrolled"] = True
                operations_applied.append(op.model_dump() if hasattr(op, "model_dump") else dict(op))

            # F. Submit Form (Disabled by Default in Phase 12)
            elif op_type == "SUBMIT_FORM":
                logger.warn(f"AUDIT EVENT [BROWSER_SUBMIT_BLOCKED] ID [{request.execution_id}]: Automatic form submission disabled")
                return self._build_blocked_result(request, "HIGH_RISK_ACTION: Automatic form submission is disabled by default in Phase 12.")

        logger.info(f"AUDIT EVENT [BROWSER_ACTION_APPLIED] ID [{request.execution_id}]: Applied {len(operations_applied)} browser operations")

        # 7. Independent Closed-Loop Verification
        verified, verify_err = self._verify_browser_postconditions(proposal, browser_state)
        if not verified:
            logger.error(f"AUDIT EVENT [BROWSER_EXECUTION_FAILED] ID [{request.execution_id}]: Verification failed: {verify_err}")
            return ExecutionResult(
                status=ExecutionStatus.REVERTED,
                execution_id=request.execution_id,
                proposal_id=proposal.proposal_id,
                workspace_id=request.workspace_id,
                previous_revision=proposal.base_revision,
                new_revision=proposal.base_revision,
                verification="FAILED",
                error=f"VERIFICATION_FAILED: {verify_err}"
            )

        logger.info(f"AUDIT EVENT [BROWSER_EXECUTION_VERIFIED] ID [{request.execution_id}]: Browser execution verified successfully")
        version_id = f"v_browser_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:6]}"

        return ExecutionResult(
            status=ExecutionStatus.COMMITTED,
            execution_id=request.execution_id,
            proposal_id=proposal.proposal_id,
            workspace_id=request.workspace_id,
            previous_revision=proposal.base_revision,
            new_revision=proposal.base_revision + 1,
            verification="PASSED",
            version_id=version_id,
            operations_applied=operations_applied
        )

    def _extract_active_origin(self, context: RelevantContext, workspace_context: Optional[Dict[str, Any]]) -> str:
        if workspace_context and "active_origin" in workspace_context:
            return workspace_context["active_origin"]
        if context.extracted_fields and "origin" in context.extracted_fields:
            return context.extracted_fields["origin"]
        if context.extracted_fields and "active_url" in context.extracted_fields:
            url = context.extracted_fields["active_url"]
            if url and url.startswith("http"):
                parsed = urllib.parse.urlparse(url)
                return f"{parsed.scheme}://{parsed.netloc}"
        return "https://example.com"

    def _extract_approved_origin(self, proposal: Proposal) -> str:
        if proposal.operations and "origin" in proposal.operations[0].parameters:
            return proposal.operations[0].parameters["origin"]
        if proposal.trace and "origin" in proposal.trace:
            return proposal.trace["origin"]
        return "https://example.com"

    def _get_browser_state(self, workspace_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if workspace_context and "browser_state" in workspace_context:
            return workspace_context["browser_state"]
        # Default mock browser state for testing
        return {
            "url": "https://example.com",
            "origin": "https://example.com",
            "elements": {
                "input#search": {"type": "text", "value": "", "disabled": False},
                "button#test": {"text": "Test Button", "clicked": False, "disabled": False},
                "select#category": {"options": ["all", "tools", "docs"], "selected": "all"}
            }
        }

    def _verify_browser_postconditions(self, proposal: Proposal, browser_state: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        for op in proposal.operations:
            op_type = op.op_type.upper()
            params = op.parameters or {}
            target = op.target or params.get("target") or ""

            if op_type == "NAVIGATE_SAFE":
                expected_url = params.get("url") or target
                if expected_url and browser_state.get("url") != expected_url:
                    return False, f"Resulting URL '{browser_state.get('url')}' does not match expected destination '{expected_url}'"

            elif op_type == "CLICK_ELEMENT":
                el_info = browser_state.get("elements", {}).get(target, {})
                if not el_info.get("clicked"):
                    return False, f"Postcondition Failed: Click on target element '{target}' was not verified."

            elif op_type == "ENTER_NON_SENSITIVE_TEXT":
                expected_val = params.get("text") or params.get("value") or ""
                el_info = browser_state.get("elements", {}).get(target, {})
                if el_info.get("value") != expected_val:
                    return False, f"Postcondition Failed: Entered text in field '{target}' does not match expected value '{expected_val}'."

            elif op_type == "SELECT_OPTION":
                expected_opt = params.get("option") or params.get("value") or ""
                el_info = browser_state.get("elements", {}).get(target, {})
                if el_info.get("selected") != expected_opt:
                    return False, f"Postcondition Failed: Selected option in '{target}' does not match expected option '{expected_opt}'."

        return True, None

    def _build_blocked_result(self, req: ExecutionRequest, reason: str) -> ExecutionResult:
        return ExecutionResult(
            status=ExecutionStatus.BLOCKED,
            execution_id=req.execution_id,
            proposal_id=req.proposal_id,
            workspace_id=req.workspace_id,
            previous_revision=req.base_revision,
            new_revision=req.base_revision,
            verification="SKIPPED",
            error=reason
        )
