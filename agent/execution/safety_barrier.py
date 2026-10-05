"""
JARVIS Python Agent Core — Phase 10 Pre-Execution Safety Barrier
Enforces token validation, emergency stop checks, revision staleness checks, domain support, protected elements, and zero execution primitives.
"""

from typing import Tuple, Optional, Dict, Any, Set
from datetime import datetime, timezone
from agent.execution.models import ExecutionRequest, ExecutionStatus, ExecutionResult
from agent.proposals.models import Proposal, ProposalStatus
from agent.context.relevance_filter import RelevantContext
from agent.core.logging import logger

CONSUMED_TOKENS: Set[str] = set()
PROTECTED_ELEMENT_IDS: Set[str] = {"card_main", "root_workspace"}

EXECUTABLE_DOMAINS: Set[str] = {"living_canvas", "vscode", "browser"}

from agent.core.operations import ALL_KNOWN_OPS as ALLOWED_PATCH_OPS

FORBIDDEN_EXECUTION_PRIMITIVES: Set[str] = {
    "run_command", "delete_file", "write_file",
    "powershell", "cmd.exe", "bash", "eval(", "exec(", "pyautogui", "pynput",
    "sendinput", "setcursorpos", "shell_exec", "subprocess"
}


class ExecutionSafetyBarrier:
    @classmethod
    def validate_execution_request(
        cls,
        request: ExecutionRequest,
        proposal: Proposal,
        context: RelevantContext,
        workspace_revision: int = 0
    ) -> Tuple[bool, Optional[str], Optional[ExecutionResult]]:
        from agent.runtime.lifecycle import runtime_manager
        
        # 1. Emergency Stop Barrier
        if runtime_manager.state.emergency_stop_state:
            logger.warning(f"Execution Safety Barrier BLOCKED [{request.execution_id}]: Emergency Stop active")
            res = cls._build_blocked_result(request, "Emergency Stop active: System is in STOPPED state")
            return False, "Emergency Stop active", res

        # 2. Executable Domain Whitelist (Living Canvas ONLY)
        domain = proposal.domain.lower()
        if domain not in EXECUTABLE_DOMAINS:
            logger.warn(f"Execution Safety Barrier BLOCKED [{request.execution_id}]: Domain '{domain}' is not executable in Phase 10")
            res = cls._build_blocked_result(request, f"UNSUPPORTED_DOMAIN: Execution is strictly limited to Living Canvas in Phase 10. Domain '{domain}' cannot be executed.")
            return False, f"Unsupported execution domain: {domain}", res

        # 3. Approval Token Validation
        from agent.execution.authorization import auth_service
        # Token validation checks signature, replay, expiration, and proposal bindings
        if not auth_service.verify_token(request.approval_token, request):
            res = cls._build_blocked_result(request, "UNAUTHORIZED: Missing, expired, mismatched or malformed ApprovalToken")
            return False, "Invalid ApprovalToken", res

        # 4. Immediate Revision & Context Staleness Check
        if proposal.domain == "living_canvas" and (proposal.base_revision != workspace_revision or request.base_revision != workspace_revision):
            logger.warn(f"Execution Safety Barrier BLOCKED [{request.execution_id}]: Base revision {request.base_revision} != Current revision {workspace_revision}")
            res = cls._build_blocked_result(request, f"STALE_PROPOSAL: Base revision ({request.base_revision}) does not match current workspace revision ({workspace_revision}). Workspace state changed after approval.")
            return False, "STALE_PROPOSAL: Workspace revision mismatch", res

        if proposal.is_stale(context.context_hash):
            res = cls._build_blocked_result(request, f"STALE_PROPOSAL: Base context hash ({proposal.base_context_hash[:8]}) does not match current context ({context.context_hash[:8]}).")
            return False, "STALE_PROPOSAL: Context hash mismatch", res

        # 5. Operation Whitelist & Safety Primitive Scanning
        for op in proposal.operations:
            if op.op_type not in ALLOWED_PATCH_OPS:
                res = cls._build_blocked_result(request, f"DISALLOWED_OPERATION: Operation type '{op.op_type}' is not permitted.")
                return False, f"Disallowed operation type: {op.op_type}", res

            # Protected Element Check
            if op.target in PROTECTED_ELEMENT_IDS and op.op_type in ["REMOVE_ELEMENT", "DELETE_ELEMENT"]:
                res = cls._build_blocked_result(request, f"PROTECTED_ELEMENT_MUTATION: Element '{op.target}' is protected and cannot be deleted.")
                return False, f"Protected element deletion prohibited: {op.target}", res

            # Zero Execution Primitives Check
            import re
            serialized_op = (str(op.parameters) + " " + op.reason + " " + op.target + " " + op.op_type).lower()
            forbidden_regexes = [
                r"\brun_command\b", r"\bdelete_file\b", r"\bwrite_file\b",
                r"\bpowershell\b", r"\bcmd\.exe\b", r"\bbash\b", r"eval\(", r"exec\(",
                r"\bpyautogui\b", r"\bpynput\b", r"\bsendinput\b", r"\bsetcursorpos\b",
                r"\bshell_exec\b", r"\bsubprocess\b"
            ]
            for pattern in forbidden_regexes:
                if re.search(pattern, serialized_op):
                    logger.error(f"Execution Safety Barrier VIOLATION [{request.execution_id}]: Execution primitive '{pattern}' in op '{op.operation_id}'")
                    res = cls._build_blocked_result(request, f"SAFETY_BARRIER_VIOLATION: Execution primitive '{pattern}' detected in operation.")
                    return False, f"Execution primitive prohibited: {pattern}", res

        token_id = request.approval_token.get('token_id', 'UNKNOWN')
        logger.info(f"Execution Safety Barrier PASSED [{request.execution_id}]: Token [{token_id}] authorized for execution")
        return True, None, None

    @classmethod
    def consume_token_atomically(cls, token_id: str) -> bool:
        """Atomically marks an ApprovalToken as consumed to prevent replay attacks."""
        from agent.execution.authorization import auth_service
        return auth_service.consume_token(token_id)

    @classmethod
    def _build_blocked_result(cls, req: ExecutionRequest, reason: str) -> ExecutionResult:
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
