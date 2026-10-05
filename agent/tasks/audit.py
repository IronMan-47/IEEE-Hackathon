"""
JARVIS Python Agent Core — Phase 15 Task Audit Logging
Structured logging for task lifecycle events.
"""

from typing import Dict, Any, Optional
from agent.core.logging import logger
from agent.tasks.models import Task, TaskStep

def _emit_runtime_event(event_type: str, task: Task, payload: Dict[str, Any] = None, step: Optional[TaskStep] = None):
    try:
        from agent.runtime.lifecycle import runtime_manager
        from agent.runtime.models import AgentEvent
        import uuid
        
        evt = AgentEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            event_type=event_type,
            runtime_id=runtime_manager.state.runtime_id,
            task_id=task.task_id,
            step_id=step.step_id if step else None,
            proposal_id=step.proposal.proposal_id if step and step.proposal else None,
            payload=payload or {}
        )
        runtime_manager.event_bus.publish(evt)
    except ImportError:
        pass # Allow tests to run if runtime not initialized

class TaskAuditLogger:
    @classmethod
    def log_created(cls, task: Task) -> None:
        _emit_runtime_event('TASK_CREATED', task)
        logger.info(
            f"AUDIT EVENT [TASK_CREATED] Task [{task.task_id}]: "
            f"Req [{task.normalized_request_id}], Text [{task.user_request[:50]}...]"
        )

    @classmethod
    def log_step_proposed(cls, task: Task, step: TaskStep) -> None:
        prop_id = step.proposal.proposal_id if step.proposal else "NONE"
        _emit_runtime_event('TASK_STEP_PROPOSED', task, {}, step)
        logger.info(
            f"AUDIT EVENT [TASK_STEP_PROPOSED] Task [{task.task_id}], Step [{step.step_id}]: "
            f"Type [{step.step_type.value}], Domain [{step.target_domain}], Proposal [{prop_id}]"
        )

    @classmethod
    def log_step_approved(cls, task: Task, step: TaskStep, token_id: str) -> None:
        _emit_runtime_event('TASK_STEP_APPROVED', task, {'token_id': token_id}, step)
        logger.info(
            f"AUDIT EVENT [TASK_STEP_APPROVED] Task [{task.task_id}], Step [{step.step_id}]: "
            f"Token [{token_id}]. Single-use authorization granted."
        )

    @classmethod
    def log_step_executed(cls, task: Task, step: TaskStep, exec_id: str, status: str) -> None:
        _emit_runtime_event('TASK_STEP_EXECUTED', task, {'execution_id': exec_id, 'status': status}, step)
        logger.info(
            f"AUDIT EVENT [TASK_STEP_EXECUTED] Task [{task.task_id}], Step [{step.step_id}]: "
            f"ExecID [{exec_id}], Status [{status}]"
        )

    @classmethod
    def log_step_verified(cls, task: Task, step: TaskStep, result: str) -> None:
        _emit_runtime_event('TASK_STEP_VERIFIED', task, {'result': result}, step)
        logger.info(
            f"AUDIT EVENT [TASK_STEP_VERIFIED] Task [{task.task_id}], Step [{step.step_id}]: "
            f"Result [{result}]"
        )

    @classmethod
    def log_reassessed(cls, task: Task, context_hash: str, steps_remaining: int) -> None:
        _emit_runtime_event('TASK_REASSESSED', task, {'context_hash': context_hash})
        logger.info(
            f"AUDIT EVENT [TASK_REASSESSED] Task [{task.task_id}]: "
            f"ContextHash [{context_hash[:8]}], StepsRemaining [{steps_remaining}]"
        )

    @classmethod
    def log_replanned(cls, task: Task, replan_count: int, new_step_count: int) -> None:
        _emit_runtime_event('TASK_REPLANNED', task, {'replan_count': replan_count})
        logger.info(
            f"AUDIT EVENT [TASK_REPLANNED] Task [{task.task_id}]: "
            f"ReplanCount [{replan_count}], NewStepCount [{new_step_count}]"
        )

    @classmethod
    def log_completed(cls, task: Task) -> None:
        _emit_runtime_event('TASK_COMPLETED', task)
        logger.info(f"AUDIT EVENT [TASK_COMPLETED] Task [{task.task_id}]: All steps successfully executed and verified.")

    @classmethod
    def log_blocked(cls, task: Task, reason: str) -> None:
        _emit_runtime_event('TASK_BLOCKED', task, {'reason': reason})
        logger.warning(f"AUDIT EVENT [TASK_BLOCKED] Task [{task.task_id}]: Reason [{reason}]")

    @classmethod
    def log_failed(cls, task: Task, error: str) -> None:
        _emit_runtime_event('TASK_FAILED', task, {'error': error})
        logger.error(f"AUDIT EVENT [TASK_FAILED] Task [{task.task_id}]: Error [{error}]")

    @classmethod
    def log_paused(cls, task: Task) -> None:
        _emit_runtime_event('TASK_PAUSED', task)
        logger.info(f"AUDIT EVENT [TASK_PAUSED] Task [{task.task_id}]: Task explicitly paused by user.")

    @classmethod
    def log_cancelled(cls, task: Task) -> None:
        _emit_runtime_event('TASK_CANCELLED', task)
        logger.info(f"AUDIT EVENT [TASK_CANCELLED] Task [{task.task_id}]: Task cancelled by user.")
