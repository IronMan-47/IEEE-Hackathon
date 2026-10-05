"""
JARVIS Python Agent Core — Phase 11 VS Code Domain Executor
Implements controlled, typed document mutations, range-based text edits, refactoring,
and code formatting for Visual Studio Code with closed-loop postcondition verification.
"""

import os
import hashlib
import uuid
import ast
from datetime import datetime, timezone
from typing import Tuple, Optional, Dict, Any, List
from agent.execution.base import BaseDomainExecutor
from agent.execution.models import ExecutionRequest, ExecutionStatus, ExecutionResult
from agent.execution.safety_barrier import ExecutionSafetyBarrier
from agent.proposals.models import Proposal
from agent.context.relevance_filter import RelevantContext
from agent.core.logging import logger

from agent.core.operations import VSCODE_OPS as ALLOWED_VSCODE_OPS

class VSCodeExecutor(BaseDomainExecutor):
    def can_execute(self, domain: str) -> bool:
        return (domain or "").lower().strip() == "vscode"

    def execute(
        self,
        request: ExecutionRequest,
        proposal: Proposal,
        context: RelevantContext,
        workspace_context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        logger.info(f"AUDIT EVENT [VSCODE_EXECUTION_REQUESTED] ID [{request.execution_id}]: Proposal [{proposal.proposal_id}]")

        # 1. Domain Check
        if not self.can_execute(proposal.domain):
            return self._build_blocked_result(
                request,
                f"UNSUPPORTED_DOMAIN: VSCodeExecutor cannot handle domain '{proposal.domain}'"
            )

        # 2. Application Availability & Context Binding Check
        app_name = (context.active_app_name or context.active_app_domain or "").lower()
        title = (context.raw_title or context.active_window_title or "").lower()

        is_vscode = (
            "vscode" in app_name or "code" in app_name or
            "visual studio code" in title or "code" in title
        )

        if not is_vscode:
            logger.warn(f"AUDIT EVENT [VSCODE_EXECUTION_BLOCKED] ID [{request.execution_id}]: Application '{app_name}' is not VS Code")
            return self._build_blocked_result(
                request,
                f"APPLICATION_UNAVAILABLE: Visual Studio Code is not active. Current app: '{context.active_app_name}'. JARVIS will not start applications automatically."
            )

        # 3. Target File Resolution & Verification
        target_file = proposal.operations[0].target if proposal.operations else (context.active_file or "example.py")
        if not target_file:
            return self._build_blocked_result(request, "INVALID_TARGET: Target file is unspecified")

        # Resolve file path
        try:
            resolved_path = self._resolve_target_path(target_file, workspace_context)
        except ValueError as e:
            logger.error(f"AUDIT EVENT [VSCODE_PATH_TRAVERSAL_BLOCKED] ID [{request.execution_id}]: {str(e)}")
            return self._build_blocked_result(request, str(e))

        # Read file content if exists
        file_exists, current_content, err_msg = self._read_file(resolved_path, workspace_context)
        if not file_exists:
            return self._build_blocked_result(request, f"FILE_NOT_FOUND: Target file '{target_file}' does not exist.")

        current_hash = hashlib.sha256(current_content.encode('utf-8')).hexdigest()

        # 4. Document & Context Conflict / Stale Detection
        if proposal.operations and "base_hash" in proposal.operations[0].parameters:
            file_base_hash = proposal.operations[0].parameters["base_hash"]
            if file_base_hash and current_hash != file_base_hash:
                logger.warn(f"AUDIT EVENT [VSCODE_DOCUMENT_CHANGED] ID [{request.execution_id}]: Content hash mismatch ({current_hash[:8]} != {file_base_hash[:8]})")
                return self._build_blocked_result(
                    request,
                    f"DOCUMENT_CHANGED: Target file '{target_file}' was modified after proposal approval (Hash mismatch)."
                )

        # 5. Global Pre-Execution Safety Barrier Validation
        valid, err_reason, barrier_result = ExecutionSafetyBarrier.validate_execution_request(
            request=request,
            proposal=proposal,
            context=context,
            workspace_revision=proposal.base_revision
        )
        if not valid and barrier_result:
            return barrier_result

        # 6. Single-Use Token Consumption (Prevent Replay Attacks)
        token_id = request.approval_token.get("token_id", "")
        if not ExecutionSafetyBarrier.consume_token_atomically(token_id):
            return self._build_blocked_result(request, f"TOKEN_REPLAY_ATTACK_PREVENTED: ApprovalToken [{token_id}] was already consumed.")

        logger.info(f"AUDIT EVENT [VSCODE_DOCUMENT_VALIDATED] ID [{request.execution_id}]: Target file [{target_file}] ready for controlled mutation")

        # 7. Apply Controlled VS Code Operations (Staged Transaction)
        pre_execution_snapshot = current_content
        mutated_content = current_content
        operations_applied = []

        try:
            for op in proposal.operations:
                op_type = op.op_type.upper()
                if op_type not in ALLOWED_VSCODE_OPS:
                    return self._build_blocked_result(request, f"UNSUPPORTED_OPERATION: VS Code operation '{op_type}' is not allowed.")

                if op_type == "CODE_CHANGE":
                    mutated_content, op_record = self._apply_code_change(mutated_content, op)
                elif op_type == "REFACTOR":
                    mutated_content, op_record = self._apply_refactor(mutated_content, op)
                elif op_type == "FORMAT_CODE":
                    mutated_content, op_record = self._apply_format_code(mutated_content, op)
                else:
                    return self._build_blocked_result(request, f"UNSUPPORTED_OPERATION: '{op_type}'")

                operations_applied.append(op_record)

            logger.info(f"AUDIT EVENT [VSCODE_EDIT_APPLIED] ID [{request.execution_id}]: Applied {len(operations_applied)} operations")

            # Write mutated content to target file / memory workspace
            self._write_file(resolved_path, mutated_content, workspace_context)

        except Exception as e:
            logger.error(f"AUDIT EVENT [VSCODE_EXECUTION_FAILED] ID [{request.execution_id}]: Edit application error: {str(e)}")
            self._write_file(resolved_path, pre_execution_snapshot, workspace_context)
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                execution_id=request.execution_id,
                proposal_id=proposal.proposal_id,
                workspace_id=request.workspace_id,
                previous_revision=proposal.base_revision,
                new_revision=proposal.base_revision,
                verification="FAILED",
                error=f"EXECUTION_ERROR: {str(e)}"
            )

        # 8. Independent Closed-Loop Postcondition Verification
        logger.info(f"AUDIT EVENT [VSCODE_EXECUTION_VERIFYING] ID [{request.execution_id}]")
        verified, verify_err = self._verify_postconditions(
            target_file=target_file,
            resolved_path=resolved_path,
            original_content=pre_execution_snapshot,
            mutated_content=mutated_content,
            proposal=proposal,
            workspace_context=workspace_context
        )

        if not verified:
            logger.error(f"AUDIT EVENT [VSCODE_EXECUTION_FAILED] ID [{request.execution_id}]: Verification failed: {verify_err}")
            # Restore pre-execution snapshot
            self._write_file(resolved_path, pre_execution_snapshot, workspace_context)
            return ExecutionResult(
                status=ExecutionStatus.REVERTED,
                execution_id=request.execution_id,
                proposal_id=proposal.proposal_id,
                workspace_id=request.workspace_id,
                previous_revision=proposal.base_revision,
                new_revision=proposal.base_revision,
                verification="FAILED",
                error=f"VERIFICATION_FAILED: {verify_err}. Target document reverted to pre-execution snapshot."
            )

        # 9. Execution Success & Version Commit Record
        logger.info(f"AUDIT EVENT [VSCODE_EXECUTION_VERIFIED] ID [{request.execution_id}]: Execution committed successfully")
        version_id = f"v_vscode_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:6]}"

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

    def _resolve_target_path(self, target_file: str, workspace_context: Optional[Dict[str, Any]]) -> str:
        ws_path = ""
        if workspace_context and isinstance(workspace_context, dict):
            ws_path = workspace_context.get("workspace_path") or workspace_context.get("path") or ""
        
        if not ws_path:
            ws_path = os.getcwd()
            
        base_dir = os.path.abspath(ws_path)
        
        if os.path.isabs(target_file):
            resolved_path = os.path.abspath(target_file)
        else:
            resolved_path = os.path.abspath(os.path.join(base_dir, target_file))
            
        if not resolved_path.startswith(base_dir + os.sep):
            # Path traversal detected or path outside workspace
            raise ValueError(f"PATH_TRAVERSAL_REJECTED: Target file '{target_file}' is outside the approved workspace '{base_dir}'.")
            
        return resolved_path

    def _read_file(self, file_path: str, workspace_context: Optional[Dict[str, Any]]) -> Tuple[bool, str, Optional[str]]:
        # In-memory mock workspace support for unit testing / headless verification
        if workspace_context and "mock_files" in workspace_context:
            mock_files = workspace_context["mock_files"]
            target_key = os.path.basename(file_path)
            if target_key in mock_files:
                return True, mock_files[target_key], None
            if file_path in mock_files:
                return True, mock_files[file_path], None

        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return True, f.read(), None
            except Exception as e:
                return False, "", str(e)
        return False, "", "File not found"

    def _write_file(self, file_path: str, content: str, workspace_context: Optional[Dict[str, Any]]) -> None:
        if workspace_context and "mock_files" in workspace_context:
            target_key = os.path.basename(file_path)
            workspace_context["mock_files"][target_key] = content
            workspace_context["mock_files"][file_path] = content
            return

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _apply_code_change(self, content: str, op: Any) -> Tuple[str, Dict[str, Any]]:
        params = op.parameters or {}
        target_content = params.get("target_content") or params.get("old_text") or ""
        replacement_content = params.get("replacement_content") or params.get("new_text") or ""

        if not target_content:
            # Full replacement or append if explicit
            if "new_content" in params:
                return params["new_content"], op.model_dump() if hasattr(op, "model_dump") else dict(op)
            raise ValueError("CODE_CHANGE operation requires 'target_content' or 'old_text'")

        if target_content not in content:
            raise ValueError(f"Target text snippet '{target_content[:30]}' not found in document")

        # Range-based exact replacement
        updated = content.replace(target_content, replacement_content, 1)
        op_dict = op.model_dump() if hasattr(op, "model_dump") else dict(op)
        return updated, op_dict

    def _apply_refactor(self, content: str, op: Any) -> Tuple[str, Dict[str, Any]]:
        params = op.parameters or {}
        target_symbol = params.get("target_symbol") or params.get("old_text") or ""
        new_symbol = params.get("new_symbol") or params.get("new_text") or ""

        if not target_symbol or not new_symbol:
            # Fallback to text snippet replace if specified
            old_t = params.get("old_text", "")
            new_t = params.get("new_text", "")
            if old_t and old_t in content:
                updated = content.replace(old_t, new_t, 1)
                return updated, op.model_dump() if hasattr(op, "model_dump") else dict(op)
            raise ValueError("REFACTOR operation requires 'target_symbol' and 'new_symbol'")

        if target_symbol not in content:
            raise ValueError(f"Target symbol '{target_symbol}' not found in document")

        updated = content.replace(target_symbol, new_symbol)
        op_dict = op.model_dump() if hasattr(op, "model_dump") else dict(op)
        return updated, op_dict

    def _apply_format_code(self, content: str, op: Any) -> Tuple[str, Dict[str, Any]]:
        # Controlled code formatting (strips trailing whitespace, normalizes end of line)
        lines = [line.rstrip() for line in content.splitlines()]
        formatted = "\n".join(lines)
        if not formatted.endswith("\n"):
            formatted += "\n"
        op_dict = op.model_dump() if hasattr(op, "model_dump") else dict(op)
        return formatted, op_dict

    def _verify_postconditions(
        self,
        target_file: str,
        resolved_path: str,
        original_content: str,
        mutated_content: str,
        proposal: Proposal,
        workspace_context: Optional[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str]]:
        # 1. Read back written file
        exists, read_back_content, err = self._read_file(resolved_path, workspace_context)
        if not exists or read_back_content != mutated_content:
            return False, "File write persistence verification failed."

        # 2. Verify operations satisfied
        for op in proposal.operations:
            op_type = op.op_type.upper()
            params = op.parameters or {}

            if op_type == "CODE_CHANGE":
                replacement = params.get("replacement_content") or params.get("new_text") or ""
                target_str = params.get("target_content") or params.get("old_text") or ""
                if replacement and replacement not in read_back_content:
                    return False, f"Verification Failed: Expected code replacement '{replacement[:20]}' not found in resulting document."
                if target_str and target_str != replacement and target_str in read_back_content:
                    return False, f"Verification Failed: Target text snippet '{target_str[:20]}' still exists in document."

            elif op_type == "REFACTOR":
                new_symbol = params.get("new_symbol") or params.get("new_text") or ""
                old_symbol = params.get("target_symbol") or params.get("old_text") or ""
                if new_symbol and new_symbol not in read_back_content:
                    return False, f"Verification Failed: Refactored symbol '{new_symbol}' not found in document."
                if old_symbol and old_symbol != new_symbol and old_symbol in read_back_content:
                    return False, f"Verification Failed: Old symbol '{old_symbol}' still present in document."

        # 3. Syntax Verification (for Python files)
        if target_file.endswith(".py"):
            try:
                ast.parse(read_back_content)
            except SyntaxError as syn_err:
                return False, f"Syntax Verification Failed: Resulting Python code is syntactically invalid: {str(syn_err)}"

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
