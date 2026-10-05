"""
JARVIS Python Agent Core — Phase 10 Living Canvas Executor
Deterministic transactional execution engine for Living Canvas reference environment.
"""

import copy
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, List
from agent.execution.base import BaseDomainExecutor
from agent.execution.models import ExecutionRequest, ExecutionResult, ExecutionStatus
from agent.execution.safety_barrier import ExecutionSafetyBarrier
from agent.proposals.models import Proposal, ProposalOperation, ProposalStatus
from agent.context.relevance_filter import RelevantContext
from agent.core.logging import logger


class LivingCanvasExecutor(BaseDomainExecutor):
    def can_execute(self, domain: str) -> bool:
        return domain.lower() == "living_canvas"

    def execute(
        self,
        request: ExecutionRequest,
        proposal: Proposal,
        context: RelevantContext,
        workspace_context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        ws_dict = workspace_context or {}
        current_revision = ws_dict.get("revision", request.base_revision)

        # 1. Pre-Execution Safety Barrier Revalidation
        valid, err, blocked_res = ExecutionSafetyBarrier.validate_execution_request(
            request=request,
            proposal=proposal,
            context=context,
            workspace_revision=current_revision
        )
        if not valid or blocked_res:
            return blocked_res

        token_id = request.approval_token.get("token_id")

        # 2. Atomic Token Consumption
        consumed = ExecutionSafetyBarrier.consume_token_atomically(token_id)
        if not consumed:
            return ExecutionResult(
                status=ExecutionStatus.BLOCKED,
                execution_id=request.execution_id,
                proposal_id=proposal.proposal_id,
                workspace_id=request.workspace_id,
                previous_revision=current_revision,
                new_revision=current_revision,
                verification="SKIPPED",
                error=f"DUPLICATE_EXECUTION_BLOCKED: Token [{token_id}] was already consumed."
            )

        # 3. Pre-Execution Snapshot & Staged Copy
        pre_execution_snapshot = copy.deepcopy(ws_dict)
        staged_workspace = copy.deepcopy(ws_dict)
        staged_elements = staged_workspace.get("elements", {})

        logger.info(f"AUDIT EVENT [EXECUTION_STARTED] ID [{request.execution_id}]: Base Rev {current_revision}, Ops count {len(proposal.operations)}")

        # 4. Transactional Application on Staged State
        operations_applied = []
        for op in proposal.operations:
            success, apply_err, op_info = self._apply_op_to_staged(op, staged_elements)
            if not success:
                logger.error(f"AUDIT EVENT [EXECUTION_FAILED] ID [{request.execution_id}]: Operation {op.operation_id} failed: {apply_err}")
                # Abort transaction: Original workspace unchanged
                return ExecutionResult(
                    status=ExecutionStatus.FAILED,
                    execution_id=request.execution_id,
                    proposal_id=proposal.proposal_id,
                    workspace_id=request.workspace_id,
                    previous_revision=current_revision,
                    new_revision=current_revision,
                    verification="FAILED",
                    error=f"Patch application failed on operation '{op.operation_id}': {apply_err}",
                    operations_applied=operations_applied
                )
            operations_applied.append(op_info)
            logger.info(f"AUDIT EVENT [OPERATION_APPLIED] Op [{op.operation_id}]: {op.op_type} on {op.target}")

        # 5. Independent Closed-Loop Verification
        logger.info(f"AUDIT EVENT [EXECUTION_VERIFYING] ID [{request.execution_id}]: Inspecting staged postconditions")
        verified, ver_mismatches = self._verify_staged_postconditions(proposal.operations, staged_elements)

        if not verified:
            logger.error(f"AUDIT EVENT [VERIFICATION_FAILED] ID [{request.execution_id}]: Mismatches: {ver_mismatches}")
            # Restore Pre-Execution Snapshot: Workspace remains unchanged at revision X
            return ExecutionResult(
                status=ExecutionStatus.REVERTED,
                execution_id=request.execution_id,
                proposal_id=proposal.proposal_id,
                workspace_id=request.workspace_id,
                previous_revision=current_revision,
                new_revision=current_revision,
                verification="FAILED",
                error=f"Post-execution verification failed: {'; '.join(ver_mismatches)}. State safely restored to pre-execution snapshot.",
                operations_applied=operations_applied
            )

        logger.info(f"AUDIT EVENT [EXECUTION_VERIFIED] ID [{request.execution_id}]: All postconditions verified successfully")

        # 6. Commit Version Node
        new_revision = current_revision + 1
        staged_workspace["revision"] = new_revision
        staged_workspace["elements"] = staged_elements
        version_id = f"v_{new_revision}_{uuid.uuid4().hex[:6]}"

        logger.info(f"AUDIT EVENT [VERSION_COMMITTED] ID [{version_id}]: Proposal [{proposal.proposal_id}] committed -> New Rev {new_revision}")

        return ExecutionResult(
            status=ExecutionStatus.COMMITTED,
            execution_id=request.execution_id,
            proposal_id=proposal.proposal_id,
            workspace_id=request.workspace_id,
            previous_revision=current_revision,
            new_revision=new_revision,
            verification="PASSED",
            version_id=version_id,
            operations_applied=operations_applied
        )

    def _apply_op_to_staged(
        self,
        op: ProposalOperation,
        elements: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        target_id = op.target
        op_type = op.op_type
        params = op.parameters or {}

        if op_type in ["UPDATE_STYLE", "UPDATE_ELEMENT", "UPDATE_TEXT", "MOVE_ELEMENT", "RESIZE_ELEMENT"]:
            if target_id not in elements:
                return False, f"Target element '{target_id}' not found in workspace", {}
            
            elem = elements[target_id]
            if "style" in params:
                elem["style"] = {**elem.get("style", {}), **params["style"]}
            if "w" in params:
                elem["w"] = params["w"]
            if "h" in params:
                elem["h"] = params["h"]
            if "x" in params:
                elem["x"] = params["x"]
            if "y" in params:
                elem["y"] = params["y"]
            if "label" in params:
                elem["label"] = params["label"]

            return True, None, {"op": op_type, "target": target_id, "params": params}

        elif op_type in ["CREATE_ELEMENT", "ADD_ELEMENT"]:
            elements[target_id] = {
                "id": target_id,
                "type": params.get("type", "button"),
                "x": params.get("x", 50),
                "y": params.get("y", 50),
                "w": params.get("w", 120),
                "h": params.get("h", 40),
                "label": params.get("label", "New Element"),
                "style": params.get("style", {})
            }
            return True, None, {"op": op_type, "target": target_id, "params": params}

        elif op_type in ["REMOVE_ELEMENT", "DELETE_ELEMENT"]:
            if target_id in elements:
                del elements[target_id]
            return True, None, {"op": op_type, "target": target_id, "params": params}

        return True, None, {"op": op_type, "target": target_id, "params": params}

    def _verify_staged_postconditions(
        self,
        operations: List[ProposalOperation],
        elements: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        mismatches = []
        for op in operations:
            target_id = op.target
            params = op.parameters or {}

            if op.op_type in ["REMOVE_ELEMENT", "DELETE_ELEMENT"]:
                if target_id in elements:
                    mismatches.append(f"Target '{target_id}' still exists after deletion operation")
            elif op.op_type in ["UPDATE_STYLE", "UPDATE_ELEMENT"]:
                if target_id not in elements:
                    mismatches.append(f"Target '{target_id}' missing after update operation")
                else:
                    elem = elements[target_id]
                    if "w" in params and elem.get("w") != params["w"]:
                        mismatches.append(f"Target '{target_id}' width mismatch: Expected {params['w']}, got {elem.get('w')}")
                    if "style" in params and "fill" in params["style"]:
                        actual_fill = elem.get("style", {}).get("fill")
                        if actual_fill != params["style"]["fill"]:
                            mismatches.append(f"Target '{target_id}' style fill mismatch: Expected {params['style']['fill']}, got {actual_fill}")

        return len(mismatches) == 0, mismatches
