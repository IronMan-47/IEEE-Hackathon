"""
JARVIS Python Agent Core — Phase 8 Hybrid Intent Classifier & Ambiguity Detector
Combines deterministic keyphrase parsing, domain target resolution, and ambiguity detection.
"""

from typing import Tuple, Optional, List, Dict, Any
from agent.intent.models import (
    IntentCategory,
    IntentConfidence,
    TargetType,
    TargetResolution,
    Intent,
    UserRequest,
    ClarificationRequest
)
from agent.context.relevance_filter import RelevantContext
from agent.core.logging import logger


class IntentClassifier:
    AMBIGUOUS_PATTERNS = [
        "fix it", "change it", "make it better", "do that", "fix this",
        "update that", "clean it", "do it", "fix", "help"
    ]

    @classmethod
    def classify(
        cls,
        user_req: UserRequest,
        context: RelevantContext,
        provider: Optional[Any] = None
    ) -> Tuple[Intent, Optional[ClarificationRequest]]:
        text_lower = user_req.text.lower().strip()

        # 1. Ambiguity Detection Check
        if text_lower in cls.AMBIGUOUS_PATTERNS or len(text_lower.split()) <= 2 and text_lower in ["fix", "change", "update", "help"]:
            if context.active_app_domain == "unknown" or not context.active_file:
                logger.info(f"Ambiguity detected for request '{user_req.text}'")
                clarification = ClarificationRequest(
                    needs_clarification=True,
                    question="Could you specify what target or issue you would like me to address?",
                    reason="The user request is ambiguous and current application context does not specify an explicit target.",
                    missing_information=["Specific file or element name", "Desired operation or bug description"]
                )
                intent = Intent(
                    intent_type=IntentCategory.UNKNOWN,
                    confidence=IntentConfidence.LOW,
                    target=TargetResolution(type=TargetType.UNKNOWN),
                    reason="Ambiguous request requires clarification"
                )
                return intent, clarification

        # 2. Target Resolution
        target_res = cls._resolve_target(text_lower, context)

        # 3. Deterministic Category Classification
        intent_cat, confidence, reason = cls._classify_category(text_lower)

        # 4. Optional LLM Refinement if configured
        if provider and confidence != IntentConfidence.HIGH:
            try:
                # LLM can offer secondary confidence boost
                pass
            except Exception as e:
                logger.warn(f"LLM Intent Classifier fallback error: {e}")

        intent = Intent(
            intent_type=intent_cat,
            confidence=confidence,
            target=target_res,
            reason=reason
        )

        return intent, None

    @classmethod
    def _resolve_target(cls, text_lower: str, context: RelevantContext) -> TargetResolution:
        domain = context.active_app_domain.lower()

        if domain == "vscode":
            if context.active_file:
                return TargetResolution(type=TargetType.ACTIVE_FILE, name=context.active_file)
            return TargetResolution(type=TargetType.CURRENT_WORKSPACE, name=context.workspace_name or "VS Code")
        elif domain == "browser":
            return TargetResolution(type=TargetType.ACTIVE_PAGE, name=context.active_window_title)
        elif domain == "living_canvas":
            return TargetResolution(type=TargetType.ACTIVE_CANVAS, name="Living Canvas Reference App")
        elif domain == "terminal":
            return TargetResolution(type=TargetType.ACTIVE_APPLICATION, name=context.active_app_name)
        elif domain == "figma":
            return TargetResolution(type=TargetType.ACTIVE_DOCUMENT, name=context.active_window_title)

        return TargetResolution(type=TargetType.ACTIVE_APPLICATION, name=context.active_app_name)

    @classmethod
    def _classify_category(cls, text_lower: str) -> Tuple[IntentCategory, IntentConfidence, str]:
        if any(kw in text_lower for kw in ["explain", "what is", "describe", "summarize", "show me what"]):
            return IntentCategory.EXPLAIN, IntentConfidence.HIGH, "Matches explain keyphrases"

        if any(kw in text_lower for kw in ["analyze", "inspect", "check error", "audit"]):
            return IntentCategory.ANALYZE, IntentConfidence.HIGH, "Matches analyze keyphrases"

        if any(kw in text_lower for kw in ["refactor", "clean up", "improve error handling", "restructure"]):
            return IntentCategory.REFACTOR, IntentConfidence.HIGH, "Matches refactor keyphrases"

        if any(kw in text_lower for kw in ["debug", "why is", "fix error", "failing", "crash", "bug"]):
            return IntentCategory.DEBUG, IntentConfidence.HIGH, "Matches debug keyphrases"

        if any(kw in text_lower for kw in ["create", "add new", "generate", "build"]):
            return IntentCategory.CREATE, IntentConfidence.HIGH, "Matches create keyphrases"

        if any(kw in text_lower for kw in ["design", "style", "layout", "cta prominent", "color"]):
            return IntentCategory.DESIGN, IntentConfidence.HIGH, "Matches design keyphrases"

        if any(kw in text_lower for kw in ["edit", "update", "modify"]):
            return IntentCategory.EDIT, IntentConfidence.MEDIUM, "Matches edit keyphrases"

        if any(kw in text_lower for kw in ["search", "find", "locate"]):
            return IntentCategory.SEARCH, IntentConfidence.HIGH, "Matches search keyphrases"

        if any(kw in text_lower for kw in ["compare", "diff"]):
            return IntentCategory.COMPARE, IntentConfidence.HIGH, "Matches compare keyphrases"

        if any(kw in text_lower for kw in ["plan", "how can", "strategy"]):
            return IntentCategory.PLAN, IntentConfidence.HIGH, "Matches plan keyphrases"

        return IntentCategory.UNKNOWN, IntentConfidence.LOW, "Generic request without explicit intent keyphrases"
