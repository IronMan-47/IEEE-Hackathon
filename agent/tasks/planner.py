"""
JARVIS Python Agent Core — Phase 15 Task Planner
Decomposes intent & grounded context into typed, bounded TaskSteps with injection defense.
"""

import uuid
import re
from typing import List, Optional, Dict, Any
from agent.tasks.models import TaskStep, TaskStepType, TaskStepStatus
from agent.context.fusion.models import GroundedContext
from agent.intent.models import UserRequest, IntentCategory
from agent.core.logging import logger


class TaskPlanner:
    PROMPT_INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"system\s+override",
        r"bypass\s+approval",
        r"delete\s+my\s+computer",
        r"format\s+[c-z]:",
        r"rm\s+-rf",
        r"drop\s+table",
        r"exec\(",
        r"eval\("
    ]

    SUPPORTED_DOMAINS = {"living_canvas", "vscode", "browser"}

    @classmethod
    def sanitize_untrusted_input(cls, text: str) -> str:
        """
        Scans and flags potential prompt injection attacks in screen/user text.
        Returns sanitized text or original text if clean.
        """
        text_lower = text.lower()
        for pattern in cls.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                logger.warning(f"AUDIT EVENT [PROMPT_INJECTION_DETECTED]: Injection pattern '{pattern}' flagged in untrusted input")
                return f"[FLAGGED_UNTRUSTED_CONTENT: Prompt injection pattern detected]"
        return text

    @classmethod
    def create_plan(
        cls,
        user_request_text: str,
        grounded_context: Optional[GroundedContext] = None,
        max_steps: int = 10
    ) -> List[TaskStep]:
        """
        Decomposes a user request and grounded context into a list of typed TaskSteps.
        """
        # Prompt injection check
        sanitized_req = cls.sanitize_untrusted_input(user_request_text)
        if "[FLAGGED_UNTRUSTED_CONTENT" in sanitized_req:
            # Create a safe analysis step flagging the injection
            return [
                TaskStep(
                    step_number=1,
                    step_type=TaskStepType.ANALYZE,
                    title="Sanitization & Safety Check",
                    description="User request contained potentially malicious injection patterns. Operations blocked.",
                    target_domain="living_canvas",
                    status=TaskStepStatus.FAILED,
                    error="Prompt Injection Security Violation: Request rejected."
                )
            ]

        # Determine target domain
        domain = "living_canvas"
        if grounded_context and grounded_context.primary_application and grounded_context.primary_application.name.lower() != "unknown application":
            app_name = grounded_context.primary_application.name.lower()
            if "vscode" in app_name or "visual studio code" in app_name or "code" in app_name:
                domain = "vscode"
            elif "chrome" in app_name or "edge" in app_name or "browser" in app_name or "firefox" in app_name:
                domain = "browser"
            elif "canvas" in app_name or "jarvis" in app_name:
                domain = "living_canvas"
            else:
                domain = "unsupported_domain"

        # Check for explicit domain mentions in user request override
        req_lower = user_request_text.lower()
        if "living canvas" in req_lower or "canvas" in req_lower:
            domain = "living_canvas"
        elif "vscode" in req_lower or "vs code" in req_lower:
            domain = "vscode"
        elif "browser" in req_lower or "website" in req_lower or "url" in req_lower or "chrome" in req_lower:
            domain = "browser"
        elif "photoshop" in req_lower or "cmd" in req_lower or "powershell" in req_lower or "excel" in req_lower:
            domain = "unsupported_domain"

        # Build steps based on request and domain
        steps: List[TaskStep] = []

        # Step 1: Perception & Analysis
        s1 = TaskStep(
            step_number=1,
            step_type=TaskStepType.ANALYZE,
            title="Perceive & Analyze Domain Context",
            description=f"Analyze active application context and visual layout for domain '{domain}'.",
            target_domain=domain,
            expected_postcondition="Domain context fused and target targets identified."
        )
        steps.append(s1)

        # Step 2: Executable action proposal step (if supported domain)
        if domain in cls.SUPPORTED_DOMAINS:
            s2 = TaskStep(
                step_number=2,
                step_type=TaskStepType.EXECUTE,
                title=f"Execute Approved Action on {domain.upper()}",
                description=f"Formulate structured proposal and execute single step on {domain}.",
                depends_on=[s1.step_id],
                target_domain=domain,
                expected_postcondition=f"Action committed to {domain} and state verified."
            )
            steps.append(s2)

            # Step 3: Verification & Summary
            s3 = TaskStep(
                step_number=3,
                step_type=TaskStepType.REPORT,
                title="Verify Results & Summarize",
                description="Verify post-execution workspace state and report task completion.",
                depends_on=[s2.step_id],
                target_domain=domain,
                expected_postcondition="Task execution completed and verified."
            )
            steps.append(s3)
        else:
            # Unsupported domain step
            s2 = TaskStep(
                step_number=2,
                step_type=TaskStepType.EXECUTE,
                title="Unsupported Domain Execution Block",
                description=f"Requested application domain '{domain}' is not supported for execution.",
                depends_on=[s1.step_id],
                target_domain="unsupported_domain",
                expected_postcondition="Execution safely blocked."
            )
            steps.append(s2)

        # Enforce budget max_steps
        if len(steps) > max_steps:
            steps = steps[:max_steps]

        return steps
