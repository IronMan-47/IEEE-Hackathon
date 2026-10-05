"""
JARVIS Python Agent Core — Phase 15 Task State Machine
Strict state transition validation and management.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from agent.tasks.models import Task, TaskStatus
from agent.core.logging import logger


class TaskStateMachine:
    # Explicit map of allowed transitions for each status
    ALLOWED_TRANSITIONS: Dict[TaskStatus, List[TaskStatus]] = {
        TaskStatus.CREATED: [
            TaskStatus.UNDERSTANDING,
            TaskStatus.CANCELLED
        ],
        TaskStatus.UNDERSTANDING: [
            TaskStatus.PLANNING,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED
        ],
        TaskStatus.PLANNING: [
            TaskStatus.AWAITING_APPROVAL,
            TaskStatus.EXECUTING,
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.BLOCKED
        ],
        TaskStatus.AWAITING_APPROVAL: [
            TaskStatus.EXECUTING,
            TaskStatus.PAUSED,
            TaskStatus.CANCELLED,
            TaskStatus.FAILED,
            TaskStatus.BLOCKED
        ],
        TaskStatus.EXECUTING: [
            TaskStatus.VERIFYING,
            TaskStatus.FAILED,
            TaskStatus.BLOCKED,
            TaskStatus.CANCELLED
        ],
        TaskStatus.VERIFYING: [
            TaskStatus.REASSESSING,
            TaskStatus.FAILED,
            TaskStatus.BLOCKED
        ],
        TaskStatus.REASSESSING: [
            TaskStatus.PLANNING,
            TaskStatus.AWAITING_APPROVAL,
            TaskStatus.EXECUTING,
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.BLOCKED,
            TaskStatus.PAUSED
        ],
        TaskStatus.PAUSED: [
            TaskStatus.AWAITING_APPROVAL,
            TaskStatus.EXECUTING,
            TaskStatus.PLANNING,
            TaskStatus.CANCELLED
        ],
        # Terminal states - no outward transitions allowed
        TaskStatus.COMPLETED: [],
        TaskStatus.BLOCKED: [],
        TaskStatus.FAILED: [],
        TaskStatus.CANCELLED: []
    }

    @classmethod
    def transition_to(
        cls,
        task: Task,
        target_status: TaskStatus,
        reason: Optional[str] = None
    ) -> Task:
        current_status = task.status
        if current_status == target_status:
            return task  # No-op if already in target state

        allowed = cls.ALLOWED_TRANSITIONS.get(current_status, [])
        if target_status not in allowed:
            err_msg = f"Invalid Task state transition: Cannot transition from {current_status.value} to {target_status.value}"
            logger.warning(f"TaskStateMachine TRANSITION BLOCKED [{task.task_id}]: {err_msg}")
            raise ValueError(err_msg)

        logger.info(f"TaskStateMachine TRANSITION [{task.task_id}]: {current_status.value} -> {target_status.value} (Reason: {reason or 'Normal progression'})")
        
        task.status = target_status
        task.updated_at = datetime.now(timezone.utc).isoformat()
        
        if reason:
            task.error = reason

        if target_status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.BLOCKED, TaskStatus.CANCELLED):
            task.completed_at = datetime.now(timezone.utc).isoformat()

        return task
