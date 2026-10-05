"""
JARVIS Python Agent Core — Phase 8 Goal & Constraint Extractor
Extracts structured Goal and explicit/inferred Constraints from user request and intent.
"""

from typing import Tuple, List
from agent.intent.models import (
    UserRequest,
    Intent,
    Goal,
    Constraint,
    ConstraintType,
    ConstraintSource,
    TargetType
)


class GoalExtractor:
    @classmethod
    def extract(cls, user_req: UserRequest, intent: Intent) -> Tuple[Goal, List[Constraint]]:
        text = user_req.text
        text_lower = text.lower()
        target_name = intent.target.name or "active target"

        # 1. Primary Goal Construction
        if intent.intent_type == "EXPLAIN":
            primary_goal = f"Explain structure and functionality of {target_name}"
            success_condition = f"Clear technical explanation provided for {target_name}"
        elif intent.intent_type == "REFACTOR":
            primary_goal = f"Refactor and improve code quality in {target_name}"
            success_condition = f"Code structure is improved while maintaining existing functionality"
        elif intent.intent_type == "DEBUG":
            primary_goal = f"Diagnose and resolve issue in {target_name}"
            success_condition = f"Root cause identified and corrective strategy proposed"
        elif intent.intent_type == "DESIGN":
            primary_goal = f"Enhance visual layout and prominence in {target_name}"
            success_condition = f"Visual elements refined according to design guidelines"
        elif intent.intent_type == "CREATE":
            primary_goal = f"Create requested component or asset in {target_name}"
            success_condition = f"New element correctly defined and positioned"
        else:
            primary_goal = f"Address request '{text}' for {target_name}"
            success_condition = f"Strategy formulated to fulfill user request"

        goal = Goal(
            primary_goal=primary_goal,
            success_condition=success_condition,
            target=intent.target.type
        )

        # 2. Constraint Extraction
        constraints: List[Constraint] = []
        added_types = set()

        # Explicit constraints checks
        if any(p in text_lower for p in ["don't change behavior", "preserve behavior", "without changing behavior", "keep functionality"]):
            constraints.append(Constraint(
                type=ConstraintType.PRESERVE_BEHAVIOR,
                source=ConstraintSource.EXPLICIT,
                description="User explicitly requested preserving existing behavior"
            ))
            added_types.add(ConstraintType.PRESERVE_BEHAVIOR)

        if any(p in text_lower for p in ["minimal change", "small change", "targeted change"]):
            constraints.append(Constraint(
                type=ConstraintType.MINIMAL_CHANGE,
                source=ConstraintSource.EXPLICIT,
                description="User explicitly requested minimal scope change"
            ))
            added_types.add(ConstraintType.MINIMAL_CHANGE)

        if any(p in text_lower for p in ["don't delete", "do not delete"]):
            constraints.append(Constraint(
                type=ConstraintType.DO_NOT_DELETE,
                source=ConstraintSource.EXPLICIT,
                description="User explicitly prohibited deletion"
            ))
            added_types.add(ConstraintType.DO_NOT_DELETE)

        if any(p in text_lower for p in ["don't rename", "do not rename"]):
            constraints.append(Constraint(
                type=ConstraintType.DO_NOT_RENAME,
                source=ConstraintSource.EXPLICIT,
                description="User explicitly prohibited renaming"
            ))
            added_types.add(ConstraintType.DO_NOT_RENAME)

        # Inferred / System Safety Constraints
        if ConstraintType.PRESERVE_BEHAVIOR not in added_types:
            constraints.append(Constraint(
                type=ConstraintType.PRESERVE_BEHAVIOR,
                source=ConstraintSource.SYSTEM_SAFETY,
                description="Default system constraint preserving existing behavior"
            ))

        constraints.append(Constraint(
            type=ConstraintType.LIMIT_SCOPE,
            source=ConstraintSource.SYSTEM_SAFETY,
            description="Limit plan scope to active context and explicit prompt"
        ))

        return goal, constraints
