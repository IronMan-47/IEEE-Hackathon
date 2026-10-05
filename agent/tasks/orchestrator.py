"""
JARVIS Python Agent Core — Phase 15 Task Orchestrator
Manages multi-step agentic workflows with strict step-by-step human approval, reassessment, and budget enforcement.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from agent.tasks.models import (
    Task,
    TaskStep,
    TaskStatus,
    TaskStepType,
    TaskStepStatus,
    ApprovalPolicy,
    TaskBudget
)
from agent.tasks.state_machine import TaskStateMachine
from agent.tasks.planner import TaskPlanner
from agent.tasks.audit import TaskAuditLogger
from agent.core.agent import JarvisAgent
from agent.intent.models import Plan, PlanStep, UserRequest, Goal, Constraint, ConstraintType, ConstraintSource
from agent.proposals.models import Proposal
from agent.execution.models import ExecutionRequest, ExecutionResult, ExecutionStatus
from agent.core.logging import logger


class TaskOrchestrator:
    def __init__(self, agent: Optional[JarvisAgent] = None):
        self.agent = agent or JarvisAgent()
        self.tasks: Dict[str, Task] = {}

    def create_task(
        self,
        user_text: str,
        perception_result: Optional[Any] = None,
        application_context: Optional[Dict[str, Any]] = None,
        visual_context: Optional[Any] = None,
        workspace_context: Optional[Dict[str, Any]] = None,
        max_steps: int = 10,
        max_replans: int = 3
    ) -> Task:
        # Fuse context first
        gctx = self.agent.fuse_context(
            perception_result=perception_result,
            application_context=application_context,
            visual_context=visual_context,
            user_text=user_text
        )

        user_req = UserRequest(text=user_text)

        task = Task(
            user_request=user_text,
            normalized_request_id=user_req.id,
            status=TaskStatus.CREATED,
            approval_policy=ApprovalPolicy.STEP_BY_STEP,
            budget=TaskBudget(max_steps=max_steps, max_replans=max_replans),
            initial_context_hash=gctx.context_hash,
            last_context_hash=gctx.context_hash,
            grounded_context=gctx
        )

        TaskAuditLogger.log_created(task)
        TaskStateMachine.transition_to(task, TaskStatus.UNDERSTANDING)

        # Generate step sequence
        steps = TaskPlanner.create_plan(
            user_request_text=user_text,
            grounded_context=gctx,
            max_steps=max_steps
        )
        task.steps = steps

        TaskStateMachine.transition_to(task, TaskStatus.PLANNING)

        # Prepare proposal for first step if executable
        if task.steps and task.steps[0].step_type == TaskStepType.EXECUTE:
            first_step = task.steps[0]
            if first_step.target_domain in TaskPlanner.SUPPORTED_DOMAINS:
                # Generate proposal for step 1
                plan_obj, _, _, _, _ = self.agent.plan_request(
                    raw_text=user_text,
                    workspace_context=workspace_context
                )
                if plan_obj:
                    proposal, _ = self.agent.generate_proposal_from_plan(
                        plan=plan_obj,
                        workspace_context=workspace_context,
                        user_req_text=user_text
                    )
                    proposal.domain = first_step.target_domain
                    first_step.proposal = proposal
                    first_step.status = TaskStepStatus.AWAITING_APPROVAL
                    TaskAuditLogger.log_step_proposed(task, first_step)
                    TaskStateMachine.transition_to(task, TaskStatus.AWAITING_APPROVAL)
                else:
                    first_step.status = TaskStepStatus.BLOCKED
                    TaskStateMachine.transition_to(task, TaskStatus.BLOCKED, "Failed to generate plan for step.")
            else:
                first_step.status = TaskStepStatus.BLOCKED
                TaskStateMachine.transition_to(
                    task,
                    TaskStatus.BLOCKED,
                    f"UNSUPPORTED_DOMAIN: Domain '{first_step.target_domain}' is not supported"
                )
                TaskAuditLogger.log_blocked(task, f"UNSUPPORTED_DOMAIN: Domain '{first_step.target_domain}' is not supported")
        elif task.steps and task.steps[0].step_type in (TaskStepType.OBSERVE, TaskStepType.ANALYZE):
            # Advance non-executable step 1
            task.steps[0].status = TaskStepStatus.COMPLETED
            task.steps[0].completed_at = datetime.now(timezone.utc).isoformat()
            if len(task.steps) > 1 and task.steps[1].step_type == TaskStepType.EXECUTE:
                task.current_step_index = 1
                exec_step = task.steps[1]
                if exec_step.target_domain in TaskPlanner.SUPPORTED_DOMAINS:
                    plan_obj, _, _, _, _ = self.agent.plan_request(
                        raw_text=user_text,
                        workspace_context=workspace_context
                    )
                    if plan_obj:
                        proposal, _ = self.agent.generate_proposal_from_plan(
                            plan=plan_obj,
                            workspace_context=workspace_context,
                            user_req_text=user_text
                        )
                        proposal.domain = exec_step.target_domain
                        exec_step.proposal = proposal
                        exec_step.status = TaskStepStatus.AWAITING_APPROVAL
                        TaskAuditLogger.log_step_proposed(task, exec_step)
                        TaskStateMachine.transition_to(task, TaskStatus.AWAITING_APPROVAL)
                else:
                    exec_step.status = TaskStepStatus.BLOCKED
                    TaskStateMachine.transition_to(
                        task,
                        TaskStatus.BLOCKED,
                        f"UNSUPPORTED_DOMAIN: Domain '{exec_step.target_domain}' is not supported"
                    )
                    TaskAuditLogger.log_blocked(task, f"UNSUPPORTED_DOMAIN: Domain '{exec_step.target_domain}' is not supported")

        self.tasks[task.task_id] = task
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    def approve_step(
        self,
        task_id: str,
        step_id: str,
        perception_context: Optional[Dict[str, Any]] = None,
        workspace_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Task, Dict[str, Any]]:
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task ID [{task_id}] not found.")

        # Strict step-by-step policy enforcement
        if task.approval_policy != ApprovalPolicy.STEP_BY_STEP:
            raise ValueError("Invalid approval policy. Only STEP_BY_STEP policy is permitted.")

        if task.status != TaskStatus.AWAITING_APPROVAL:
            raise ValueError(f"Task [{task_id}] is not awaiting approval. Current status: {task.status.value}")

        current_step = task.steps[task.current_step_index]
        if current_step.step_id != step_id:
            raise ValueError(f"Step ID [{step_id}] does not match current pending step [{current_step.step_id}].")

        if not current_step.proposal:
            raise ValueError(f"Step [{step_id}] does not have an associated proposal for approval.")

        accepted_prop, token, _ = self.agent.accept_proposal_phase9(
            proposal=current_step.proposal,
            perception_context=perception_context,
            workspace_context=workspace_context
        )

        current_step.proposal = accepted_prop
        current_step.approval_token = token
        current_step.status = TaskStepStatus.APPROVED

        TaskAuditLogger.log_step_approved(task, current_step, token.get("token_id", "UNKNOWN"))
        return task, token

    def execute_step(
        self,
        task_id: str,
        step_id: str,
        perception_context: Optional[Dict[str, Any]] = None,
        workspace_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Task, ExecutionResult]:
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task ID [{task_id}] not found.")

        current_step = task.steps[task.current_step_index]
        if current_step.step_id != step_id:
            raise ValueError(f"Step ID [{step_id}] does not match active step [{current_step.step_id}].")

        # Check step budget
        task.budget.current_steps += 1
        if task.budget.current_steps > task.budget.max_steps:
            reason = f"BUDGET_EXCEEDED: Task exceeded maximum allowed step budget ({task.budget.max_steps})"
            TaskStateMachine.transition_to(task, TaskStatus.BLOCKED, reason)
            TaskAuditLogger.log_blocked(task, reason)
            res = ExecutionResult(
                status=ExecutionStatus.BLOCKED,
                execution_id="none",
                proposal_id=current_step.proposal.proposal_id if current_step.proposal else "none",
                workspace_id="checkout_demo",
                previous_revision=0,
                new_revision=0,
                verification="FAILED",
                error=reason
            )
            return task, res

        # Check domain support
        if current_step.target_domain not in TaskPlanner.SUPPORTED_DOMAINS:
            reason = f"UNSUPPORTED_DOMAIN: Domain '{current_step.target_domain}' is not supported for execution."
            current_step.status = TaskStepStatus.BLOCKED
            TaskStateMachine.transition_to(task, TaskStatus.BLOCKED, reason)
            TaskAuditLogger.log_blocked(task, reason)
            res = ExecutionResult(
                status=ExecutionStatus.BLOCKED,
                execution_id="none",
                proposal_id=current_step.proposal.proposal_id if current_step.proposal else "none",
                workspace_id="checkout_demo",
                previous_revision=0,
                new_revision=0,
                verification="FAILED",
                error=reason
            )
            return task, res

        # Validate token presence
        if not current_step.approval_token:
            reason = f"UNAUTHORIZED: Step [{step_id}] missing required single-use ApprovalToken."
            current_step.status = TaskStepStatus.FAILED
            TaskStateMachine.transition_to(task, TaskStatus.FAILED, reason)
            TaskAuditLogger.log_failed(task, reason)
            res = ExecutionResult(
                status=ExecutionStatus.BLOCKED,
                execution_id="none",
                proposal_id=current_step.proposal.proposal_id if current_step.proposal else "none",
                workspace_id="checkout_demo",
                previous_revision=0,
                new_revision=0,
                verification="FAILED",
                error=reason
            )
            return task, res

        # Transition to EXECUTING
        TaskStateMachine.transition_to(task, TaskStatus.EXECUTING)
        current_step.status = TaskStepStatus.EXECUTING

        # Construct execution request
        prop = current_step.proposal
        exec_req = ExecutionRequest(
            proposal_id=prop.proposal_id,
            approval_token=current_step.approval_token,
            workspace_id="checkout_demo",
            base_revision=prop.base_revision,
            base_context_id=prop.base_context_id,
            base_context_hash=prop.base_context_hash
        )

        exec_res = self.agent.execute_proposal(
            exec_request=exec_req,
            proposal=prop,
            perception_context=perception_context,
            workspace_context=workspace_context
        )

        current_step.execution_result = exec_res
        TaskAuditLogger.log_step_executed(task, current_step, exec_res.execution_id, exec_res.status.value)

        # Transition to VERIFYING
        TaskStateMachine.transition_to(task, TaskStatus.VERIFYING)
        current_step.status = TaskStepStatus.VERIFYING

        if exec_res.status in (ExecutionStatus.VERIFIED, ExecutionStatus.COMMITTED):
            current_step.verification_status = "PASSED"
            current_step.status = TaskStepStatus.COMPLETED
            current_step.completed_at = datetime.now(timezone.utc).isoformat()
            TaskAuditLogger.log_step_verified(task, current_step, "PASSED")
        else:
            current_step.verification_status = "FAILED"
            current_step.status = TaskStepStatus.FAILED
            TaskAuditLogger.log_step_verified(task, current_step, "FAILED")

        # Transition to REASSESSING
        TaskStateMachine.transition_to(task, TaskStatus.REASSESSING)

        # Re-perceive desktop context for state fusion
        new_gctx = self.agent.fuse_context(
            user_text=task.user_request
        )
        task.last_context_hash = new_gctx.context_hash
        task.verification_history.append({
            "step_id": step_id,
            "status": current_step.verification_status,
            "context_hash": new_gctx.context_hash,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        TaskAuditLogger.log_reassessed(task, new_gctx.context_hash, len(task.steps) - task.current_step_index - 1)

        # Check for failure & replan
        if current_step.verification_status == "FAILED" or exec_res.status in (ExecutionStatus.FAILED, ExecutionStatus.BLOCKED):
            if task.budget.current_replans < task.budget.max_replans:
                task.budget.current_replans += 1
                TaskAuditLogger.log_replanned(task, task.budget.current_replans, len(task.steps))
                # Re-plan remaining steps
                new_steps = TaskPlanner.create_plan(
                    user_request_text=task.user_request,
                    grounded_context=new_gctx,
                    max_steps=task.budget.max_steps
                )
                task.steps = new_steps
                task.current_step_index = 0
                TaskStateMachine.transition_to(task, TaskStatus.PLANNING)

                if task.steps and task.steps[0].step_type == TaskStepType.EXECUTE:
                    first_step = task.steps[0]
                    if first_step.target_domain in TaskPlanner.SUPPORTED_DOMAINS:
                        plan_obj, _, _, _, _ = self.agent.plan_request(
                            raw_text=task.user_request,
                            workspace_context=workspace_context
                        )
                        if plan_obj:
                            proposal, _ = self.agent.generate_proposal_from_plan(
                                plan=plan_obj,
                                workspace_context=workspace_context,
                                user_req_text=task.user_request
                            )
                            proposal.domain = first_step.target_domain
                            first_step.proposal = proposal
                            first_step.status = TaskStepStatus.AWAITING_APPROVAL
                            TaskAuditLogger.log_step_proposed(task, first_step)
                            TaskStateMachine.transition_to(task, TaskStatus.AWAITING_APPROVAL)
            else:
                err_msg = f"REPLAN_BUDGET_EXCEEDED: Task exceeded maximum allowed replans ({task.budget.max_replans})"
                TaskStateMachine.transition_to(task, TaskStatus.FAILED, err_msg)
                TaskAuditLogger.log_failed(task, err_msg)
        else:
            # Advance to next step or complete task
            task.current_step_index += 1
            if task.current_step_index >= len(task.steps):
                TaskStateMachine.transition_to(task, TaskStatus.COMPLETED)
                TaskAuditLogger.log_completed(task)
            else:
                next_step = task.steps[task.current_step_index]
                if next_step.step_type == TaskStepType.EXECUTE:
                    if not next_step.proposal and next_step.target_domain in TaskPlanner.SUPPORTED_DOMAINS:
                        plan_obj, _, _, _, _ = self.agent.plan_request(
                            raw_text=task.user_request,
                            workspace_context=workspace_context
                        )
                        if plan_obj:
                            proposal, _ = self.agent.generate_proposal_from_plan(
                                plan=plan_obj,
                                workspace_context=workspace_context,
                                user_req_text=task.user_request
                            )
                            proposal.domain = next_step.target_domain
                            next_step.proposal = proposal
                    next_step.status = TaskStepStatus.AWAITING_APPROVAL
                    TaskAuditLogger.log_step_proposed(task, next_step)
                    TaskStateMachine.transition_to(task, TaskStatus.AWAITING_APPROVAL)
                else:
                    next_step.status = TaskStepStatus.COMPLETED
                    next_step.completed_at = datetime.now(timezone.utc).isoformat()
                    task.current_step_index += 1
                    if task.current_step_index >= len(task.steps):
                        TaskStateMachine.transition_to(task, TaskStatus.COMPLETED)
                        TaskAuditLogger.log_completed(task)

        return task, exec_res

    def pause_task(self, task_id: str) -> Task:
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task ID [{task_id}] not found.")
        TaskStateMachine.transition_to(task, TaskStatus.PAUSED, "Paused by user")
        TaskAuditLogger.log_paused(task)
        return task

    def cancel_task(self, task_id: str) -> Task:
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task ID [{task_id}] not found.")
        TaskStateMachine.transition_to(task, TaskStatus.CANCELLED, "Cancelled by user")
        TaskAuditLogger.log_cancelled(task)
        return task

    def resume_task(self, task_id: str) -> Task:
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task ID [{task_id}] not found.")
        if task.status != TaskStatus.PAUSED:
            raise ValueError(f"Task [{task_id}] is not paused. Current status: {task.status.value}")
        
        current_step = task.steps[task.current_step_index] if task.current_step_index < len(task.steps) else None
        if current_step and current_step.proposal and not current_step.approval_token:
            TaskStateMachine.transition_to(task, TaskStatus.AWAITING_APPROVAL, "Resumed by user")
        else:
            TaskStateMachine.transition_to(task, TaskStatus.EXECUTING, "Resumed by user")
        return task

    def modify_step(
        self,
        task_id: str,
        step_id: str,
        instructions: str,
        perception_context: Optional[Dict[str, Any]] = None,
        workspace_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Task, "TaskModification"]:
        from agent.explainability.models import TaskModification
        import uuid

        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task ID [{task_id}] not found.")
        
        if task.status != TaskStatus.AWAITING_APPROVAL:
            raise ValueError(f"Task [{task_id}] is not awaiting approval. Current status: {task.status.value}")
        
        current_step = task.steps[task.current_step_index]
        if current_step.step_id != step_id:
            raise ValueError(f"Step ID [{step_id}] does not match current pending step [{current_step.step_id}].")

        # Invalidate current step (skip it)
        current_step.status = TaskStepStatus.SKIPPED
        current_step.error = f"Modified by user: {instructions}"

        # Fuse context again, conceptually incorporating instructions
        new_gctx = self.agent.fuse_context(
            user_text=f"{task.user_request} (Correction: {instructions})",
            perception_result=perception_context,
            visual_context=None,
            application_context=None
        )
        task.last_context_hash = new_gctx.context_hash

        # Generate a new immutable step
        new_step_id = f"step_{uuid.uuid4().hex[:6]}"
        new_step = TaskStep(
            step_id=new_step_id,
            step_number=current_step.step_number,
            step_type=current_step.step_type,
            title=f"{current_step.title} (Modified)",
            description=f"Modified according to: {instructions}",
            depends_on=current_step.depends_on,
            target_domain=current_step.target_domain
        )
        
        # Replace the step in the list (maintaining immutability of the old object, replacing the reference)
        # We could also insert it, but for simplicity, we replace at the index since the old one is SKIPPED.
        # Actually, let's keep the old one and insert the new one after it? The prompt says "invalidate the old target, update grounded context, regenerate a new immutable step/proposal, and demand fresh approval."
        # We will insert the new step at the current index and keep the skipped one? Let's just insert it.
        task.steps.insert(task.current_step_index + 1, new_step)
        task.current_step_index += 1

        # Regenerate proposal for the new step
        if new_step.target_domain in TaskPlanner.SUPPORTED_DOMAINS:
            plan_obj, _, _, _, _ = self.agent.plan_request(
                raw_text=f"{task.user_request} (Correction: {instructions})",
                workspace_context=workspace_context
            )
            if plan_obj:
                proposal, _ = self.agent.generate_proposal_from_plan(
                    plan=plan_obj,
                    workspace_context=workspace_context,
                    user_req_text=f"{task.user_request} (Correction: {instructions})"
                )
                proposal.domain = new_step.target_domain
                new_step.proposal = proposal
                new_step.status = TaskStepStatus.AWAITING_APPROVAL
                TaskAuditLogger.log_step_proposed(task, new_step)
            else:
                new_step.status = TaskStepStatus.BLOCKED
                TaskStateMachine.transition_to(task, TaskStatus.BLOCKED, "Failed to generate modified plan.")
        
        modification = TaskModification(
            modification_id=f"mod_{uuid.uuid4().hex[:6]}",
            original_step_id=current_step.step_id,
            new_step_id=new_step.step_id,
            reason=instructions
        )

        return task, modification

    def initiate_cross_app_transition(
        self,
        task_id: str,
        target_application: str,
        relevant_evidence: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Phase 19: Initiates a handoff from the current application context to a new target application.
        Sanitizes data and creates a handoff payload, updating the task.
        """
        task = self.tasks.get(task_id)
        if not task:
            return None

        from agent.context.cross_application import CrossAppHandoffManager
        
        handoff = CrossAppHandoffManager.create_handoff(
            workflow_id=task.task_id,
            source_app=task.grounded_context.primary_application.name if task.grounded_context else "unknown",
            target_app=target_application,
            source_context=task.grounded_context,
            relevant_evidence=relevant_evidence
        )

        task.active_handoff = handoff.model_dump()
        return task.active_handoff

    def consume_cross_app_handoff(
        self,
        task_id: str,
        target_context: Any
    ) -> bool:
        """
        Phase 19: Re-grounds the task in the target application context using the handoff evidence.
        """
        task = self.tasks.get(task_id)
        if not task or not task.active_handoff:
            return False

        from agent.context.cross_application import CrossAppHandoffManager, CrossApplicationContext, HandoffStatus
        
        handoff = CrossApplicationContext(**task.active_handoff)
        success = CrossAppHandoffManager.verify_target_context(handoff, target_context)
        
        task.active_handoff = handoff.model_dump()
        
        if not success:
            task.status = TaskStatus.BLOCKED
            task.error = f"CROSS_APP_CONFLICT: Expected target {handoff.target_application} but found {target_context.primary_application.name}"
            try:
                from agent.runtime.lifecycle import runtime_manager
                runtime_manager._emit("CROSS_APP_CONFLICT_DETECTED", {"task_id": task_id, "error": task.error})
            except ImportError:
                pass
            return False
            
        try:
            from agent.runtime.lifecycle import runtime_manager
            runtime_manager._emit("CROSS_APP_CONTEXT_FUSED", {"task_id": task_id, "target_context": target_context.context_id})
        except ImportError:
            pass

        # Update the task's active grounded context and clear active handoff
        task.grounded_context = target_context
        # We leave the handoff data in the active step's evidence/handoff field
        if task.current_step_index < len(task.steps):
            task.steps[task.current_step_index].cross_app_handoff = handoff.model_dump()
            
        task.active_handoff = None
        task.last_context_hash = target_context.context_hash
        return True
