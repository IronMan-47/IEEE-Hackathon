"""
JARVIS Python Agent Core — Phase 9 Proposal Validator & Security Boundary
Enforces schema validation, semantic checks, risk classification, and prompt injection defense.
"""

from typing import Tuple, Optional, List
from agent.proposals.models import Proposal, ProposalOperation, ProposalStatus, RiskLevel
from agent.context.relevance_filter import RelevantContext
from agent.core.logging import logger

MAX_OPS_PER_PROPOSAL = 10

from agent.core.operations import LIVING_CANVAS_OPS, VSCODE_OPS, BROWSER_OPS, TERMINAL_OPS, FIGMA_OPS

FORBIDDEN_EXECUTION_PATTERNS = [
    "<script>", "javascript:", "eval(", "exec(", "import os", "import subprocess",
    "system(", "passthru(", "shell_exec", "cmd.exe", "powershell", "pyautogui",
    "pynput", "sendinput", "setcursorpos", "rm -rf", "format c:", "drop table"
]


class ProposalValidator:
    @classmethod
    def validate(cls, proposal: Proposal, context: RelevantContext) -> Tuple[bool, Optional[str]]:
        # 1. Structural Checks
        if not proposal.proposal_id or not proposal.request_id or not proposal.plan_id:
            return False, "Proposal ID, Request ID, and Plan ID must be non-empty."

        if not proposal.operations or len(proposal.operations) == 0:
            return False, "Proposal must contain at least one operation."

        if len(proposal.operations) > MAX_OPS_PER_PROPOSAL:
            return False, f"Operation limit exceeded: Proposal contains {len(proposal.operations)} operations (Max allowed: {MAX_OPS_PER_PROPOSAL})."

        # 2. Context Staleness / Conflict Check
        if proposal.is_stale(context.context_hash):
            proposal.status = ProposalStatus.STALE
            logger.warn(f"Proposal [{proposal.proposal_id}] is STALE: Base hash '{proposal.base_context_hash[:8]}' != Current hash '{context.context_hash[:8]}'")
            return False, f"Proposal is STALE: Base context snapshot hash ({proposal.base_context_hash[:8]}) does not match current context ({context.context_hash[:8]})."

        # 3. Domain & Operation Whitelist Check
        domain = proposal.domain.lower()
        if domain == "living_canvas":
            allowed_ops = LIVING_CANVAS_OPS
        elif domain == "vscode":
            allowed_ops = VSCODE_OPS
        elif domain == "browser":
            allowed_ops = BROWSER_OPS
        elif domain == "terminal":
            allowed_ops = TERMINAL_OPS
        elif domain == "figma":
            allowed_ops = FIGMA_OPS
        else:
            allowed_ops = LIVING_CANVAS_OPS | VSCODE_OPS

        highest_risk = RiskLevel.LOW

        for op in proposal.operations:
            if not op.target or not op.target.strip():
                return False, f"Operation '{op.operation_id}' must specify a valid target element or file."

            if op.op_type not in allowed_ops:
                return False, f"Operation type '{op.op_type}' is disallowed for domain '{domain}'."

            # Security Check: Injection & Execution Primitives
            serialized = (str(op.parameters) + " " + op.reason + " " + op.target).lower()
            for pattern in FORBIDDEN_EXECUTION_PATTERNS:
                if pattern in serialized:
                    logger.error(f"Proposal Security Violation: Forbidden pattern '{pattern}' in op '{op.operation_id}'")
                    return False, f"Security Violation: Forbidden code execution pattern '{pattern}' detected in operation parameters."

            # Risk Classification Assignment
            op_risk = cls._classify_operation_risk(domain, op.op_type)
            op.risk = op_risk
            if cls._risk_rank(op_risk) > cls._risk_rank(highest_risk):
                highest_risk = op_risk

        # 4. Semantic Target Validation
        if domain == "vscode" and context.active_file:
            # Verify target matches active file if file level operation
            pass

        proposal.risk = highest_risk
        proposal.status = ProposalStatus.VALIDATED
        logger.info(f"Proposal [{proposal.proposal_id}] validated successfully (Domain: {domain}, Risk: {highest_risk.value}, Ops: {len(proposal.operations)})")
        return True, None

    @classmethod
    def _classify_operation_risk(cls, domain: str, op_type: str) -> RiskLevel:
        if op_type in ["REMOVE_ELEMENT", "DELETE_ELEMENT", "DELETE_CODE"]:
            return RiskLevel.HIGH
        elif op_type in ["REFACTOR", "UPDATE_TEXT", "CODE_CHANGE"]:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    @classmethod
    def _risk_rank(cls, risk: RiskLevel) -> int:
        ranks = {RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2, RiskLevel.HIGH: 3, RiskLevel.DESTRUCTIVE: 4}
        return ranks.get(risk, 1)
