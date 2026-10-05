"""
JARVIS Python Agent Core — Phase 8 Plan Validator
Strictly enforces structural validity, scope validity, and safety barriers (ZERO execution primitives).
"""

from typing import Tuple, List, Optional
from agent.intent.models import Plan, PlanStepType
from agent.core.logging import logger


class PlanValidator:
    EXECUTION_PRIMITIVES = [
        "click", "type", "press_key", "run_command", "delete_file", "write_file",
        "shell", "powershell", "cmd.exe", "bash", "eval(", "exec(", "mouse_move",
        "click_at", "keyboard_inject", "launch_app", "open_url"
    ]

    @classmethod
    def validate(cls, plan: Plan) -> Tuple[bool, Optional[str]]:
        # 1. Structural Checks
        if not plan.plan_id or not plan.request_id:
            return False, "Plan ID and Request ID must be non-empty."

        if not plan.context_hash or not plan.context_snapshot_id:
            return False, "Plan must reference a non-empty context snapshot and context hash."

        if not plan.goal or not plan.goal.primary_goal.strip():
            return False, "Plan goal must be non-empty."

        if not plan.steps or len(plan.steps) == 0:
            return False, "Plan must contain at least one step."

        # 2. Step Type & Safety Checks
        valid_step_types = set(PlanStepType)

        for step in plan.steps:
            if not step.id or not step.description.strip():
                return False, f"Step ID '{step.id}' contains invalid or empty description."

            if step.type not in valid_step_types:
                return False, f"Step '{step.id}' has invalid step type '{step.type}'."

            # Safety Barrier: Check for execution primitives in descriptions or step definitions
            desc_lower = step.description.lower()
            for primitive in cls.EXECUTION_PRIMITIVES:
                if primitive in desc_lower:
                    logger.error(f"Plan Safety Boundary Violation: Primitive '{primitive}' detected in step '{step.id}'")
                    return False, f"Safety Barrier Violation: Execution primitive '{primitive}' is not permitted in Phase 8 plan steps."

        logger.info(f"Plan [{plan.plan_id}] successfully validated: {len(plan.steps)} steps")
        return True, None
