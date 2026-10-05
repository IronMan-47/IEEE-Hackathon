"""
JARVIS Python Agent Core — Phase 8 Reasoning Planner
Generates structured non-executable plans and supports human plan modifications and acceptance.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Any, Tuple
from agent.intent.models import (
    UserRequest,
    Intent,
    Goal,
    Constraint,
    Plan,
    PlanStep,
    PlanStepType,
    PlanAuthor,
    PlanStatus,
    IntentCategory
)
from agent.context.relevance_filter import RelevantContext
from agent.reasoning.plan_validator import PlanValidator
from agent.core.logging import logger


class Planner:
    def __init__(self, provider: Optional[Any] = None):
        self.provider = provider

    def plan(
        self,
        user_req: UserRequest,
        context: RelevantContext,
        intent: Intent,
        goal: Goal,
        constraints: List[Constraint]
    ) -> Plan:
        target_name = intent.target.name or "active workspace"
        steps = self._generate_steps(user_req, context, intent, goal)

        reasoning_summary = (
            f"Plan formulated for '{intent.intent_type.value}' intent targeting {target_name}. "
            f"Primary goal is '{goal.primary_goal}' with {len(constraints)} active constraints."
        )

        plan_id = f"plan_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:6]}"

        plan = Plan(
            plan_id=plan_id,
            request_id=user_req.id,
            created_at=datetime.now(timezone.utc).isoformat(),
            context_snapshot_id=context.context_id,
            context_hash=context.context_hash,
            intent=intent.intent_type,
            goal=goal,
            constraints=constraints,
            steps=steps,
            reasoning_summary=reasoning_summary,
            version=1,
            author=PlanAuthor.AI,
            status=PlanStatus.DRAFT
        )

        valid, err = PlanValidator.validate(plan)
        if not valid:
            logger.error(f"Plan validation failed during planning: {err}")
            raise ValueError(f"Invalid plan generated: {err}")

        plan.status = PlanStatus.VALIDATED
        return plan

    def modify_plan(self, original_plan: Plan, new_steps: List[PlanStep]) -> Plan:
        modified_plan = Plan(
            plan_id=f"plan_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:6]}",
            request_id=original_plan.request_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            context_snapshot_id=original_plan.context_snapshot_id,
            context_hash=original_plan.context_hash,
            intent=original_plan.intent,
            goal=original_plan.goal,
            constraints=original_plan.constraints,
            steps=new_steps,
            reasoning_summary=f"Human modified strategy based on plan {original_plan.plan_id}",
            version=original_plan.version + 1,
            author=PlanAuthor.HUMAN_MODIFIED,
            parent_plan_id=original_plan.plan_id,
            status=PlanStatus.DRAFT
        )

        valid, err = PlanValidator.validate(modified_plan)
        if not valid:
            raise ValueError(f"Modified plan failed validation: {err}")

        modified_plan.status = PlanStatus.VALIDATED
        return modified_plan

    def accept_plan(self, plan: Plan) -> Plan:
        plan.status = PlanStatus.ACCEPTED
        logger.info(f"Plan [{plan.plan_id}] accepted by user as strategy")
        return plan

    def _generate_steps(
        self,
        user_req: UserRequest,
        context: RelevantContext,
        intent: Intent,
        goal: Goal
    ) -> List[PlanStep]:
        target_name = intent.target.name or "active workspace"
        
        fallback_steps = [
            PlanStep(
                id="step_1",
                type=PlanStepType.OBSERVE,
                description=f"Gather perception metadata and context snapshot for {target_name}",
                target_id=target_name,
                reason="Establish baseline context"
            ),
            PlanStep(
                id="step_2",
                type=PlanStepType.ANALYZE,
                description=f"Analyze user request '{user_req.text}' against target state",
                reason="Identify requirements and potential constraints"
            ),
            PlanStep(
                id="step_3",
                type=PlanStepType.PROPOSE,
                description=f"Prepare candidate plan and strategy proposal",
                reason="Structure solution for human evaluation"
            ),
            PlanStep(
                id="step_4",
                type=PlanStepType.VERIFY,
                description=f"Verify alignment with user goal and safety policies",
                reason="Confirm plan safety before presenting to user"
            )
        ]
        
        if self.provider:
            from agent.context.workspace_context import WorkspaceContextModel
            ws_ctx = WorkspaceContextModel({"activeAppDomain": context.active_app_domain, "activeFile": context.active_file, "elements": context.elements})
            success, plan_dict, err = self.provider.generate_plan(ws_ctx, user_req.text)
            if success and plan_dict and "steps" in plan_dict:
                steps = []
                for s in plan_dict["steps"]:
                    steps.append(PlanStep(
                        id=s.get("id", "step_1"),
                        type=s.get("type", "PROPOSE"),
                        description=s.get("description", "Generated step"),
                        target_id=s.get("target_id", target_name),
                        reason=s.get("reason", "")
                    ))
                return steps
                
        return fallback_steps