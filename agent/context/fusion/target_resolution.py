"""
JARVIS Python Agent Core — Phase 14 Target & Deictic Reference Resolution
Resolves vague or deictic references ("this", "that", "here", "this file", "this button", "this error", "the page I'm viewing")
to precise TargetReference models with application binding and ambiguity detection.
"""

from typing import Optional, Dict, Any, List, Tuple
from pydantic import BaseModel, Field, ConfigDict
from agent.perception.visual.models import BoundingBox, VisualElement, VisualElementType
from agent.context.fusion.provenance import ProvenanceTag
from agent.context.fusion.models import GroundedContext


class TargetReference(BaseModel):
    target_id: str
    target_type: str = Field(default="UNKNOWN")
    source: ProvenanceTag = Field(default=ProvenanceTag.DERIVED)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    provenance: ProvenanceTag = Field(default=ProvenanceTag.DERIVED)
    bounds: Optional[BoundingBox] = Field(default=None)
    application_identity: str = Field(default="")
    context_binding: Dict[str, Any] = Field(default_factory=dict)
    is_ambiguous: bool = Field(default=False)
    candidate_targets: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(frozen=False)


DEICTIC_KEYWORDS = {
    "this", "that", "here", "there", "this button", "this file", "this error",
    "the selected item", "the current page", "the active file", "the button"
}


class TargetResolver:
    @staticmethod
    def resolve_target(
        user_text: str,
        grounded_context: GroundedContext
    ) -> Tuple[Optional[TargetReference], bool, Optional[str]]:
        """
        Resolves user request text to a precise TargetReference.
        Returns (TargetReference, clarification_required: bool, clarification_question: Optional[str]).
        """
        if not user_text:
            return None, False, None

        q_lower = user_text.lower().strip()
        app_name = grounded_context.primary_application.name.lower()
        app_ctx = grounded_context.application_context
        vctx = grounded_context.visual_context
        visual_elements = grounded_context.relevant_elements or (vctx.elements if vctx else [])

        # 1. Error / Exception Grounding ("this error", "fix this error", "why is this failing")
        if any(kw in q_lower for kw in ["error", "failing", "exception", "bug", "crash"]):
            # Look for error visual element or OCR text or active document error
            error_elems = [e for e in visual_elements if e.type == VisualElementType.DIALOG or "error" in (e.text or "").lower()]
            if error_elems:
                best_err = error_elems[0]
                target_ref = TargetReference(
                    target_id=best_err.id,
                    target_type="ERROR_DIALOG",
                    source=best_err.provenance,
                    confidence=best_err.confidence,
                    provenance=best_err.provenance,
                    bounds=best_err.bounds,
                    application_identity=app_name,
                    context_binding={"text": best_err.text, "application": app_name}
                )
                return target_ref, False, None

            # Fallback to active file context error if VS Code
            active_file = app_ctx.get("active_file") or app_ctx.get("file")
            if active_file:
                target_ref = TargetReference(
                    target_id=f"file:{active_file}",
                    target_type="CODE_FILE",
                    source=ProvenanceTag.VS_CODE_ADAPTER,
                    confidence=0.9,
                    provenance=ProvenanceTag.VS_CODE_ADAPTER,
                    application_identity=app_name,
                    context_binding={"file": active_file}
                )
                return target_ref, False, None

        # 2. Button Target Resolution ("this button", "click this button", "make this button larger")
        if any(kw in q_lower for kw in ["button", "btn"]):
            buttons = [e for e in visual_elements if e.type == VisualElementType.BUTTON]
            if len(buttons) == 1:
                b = buttons[0]
                return TargetReference(
                    target_id=b.id,
                    target_type="BUTTON",
                    source=b.provenance,
                    confidence=b.confidence,
                    provenance=b.provenance,
                    bounds=b.bounds,
                    application_identity=app_name,
                    context_binding={"text": b.text}
                ), False, None
            elif len(buttons) > 1:
                # Ambiguous buttons! Check if user query matches button text
                matched = [b for b in buttons if b.text and b.text.lower() in q_lower]
                if len(matched) == 1:
                    b = matched[0]
                    return TargetReference(
                        target_id=b.id,
                        target_type="BUTTON",
                        source=b.provenance,
                        confidence=b.confidence,
                        provenance=b.provenance,
                        bounds=b.bounds,
                        application_identity=app_name,
                        context_binding={"text": b.text}
                    ), False, None
                else:
                    candidates = [{"id": b.id, "text": b.text or b.id, "bounds": b.bounds.model_dump()} for b in buttons]
                    question = f"I found {len(buttons)} visible buttons ({', '.join([c['text'] for c in candidates])}). Which button do you mean?"
                    ambiguous_target = TargetReference(
                        target_id="ambiguous_buttons",
                        target_type="BUTTON",
                        source=ProvenanceTag.VISION_MODEL,
                        confidence=0.5,
                        provenance=ProvenanceTag.VISION_MODEL,
                        is_ambiguous=True,
                        candidate_targets=candidates
                    )
                    return ambiguous_target, True, question

        # 3. File Target Resolution ("this file", "edit this file")
        if "file" in q_lower or "code" in q_lower:
            active_file = app_ctx.get("active_file") or app_ctx.get("file")
            if active_file:
                return TargetReference(
                    target_id=f"file:{active_file}",
                    target_type="CODE_FILE",
                    source=ProvenanceTag.VS_CODE_ADAPTER,
                    confidence=0.95,
                    provenance=ProvenanceTag.VS_CODE_ADAPTER,
                    application_identity=app_name,
                    context_binding={"file": active_file}
                ), False, None

        # 4. Deictic Generic Target ("this", "that", "here")
        if any(w in q_lower.split() for w in ["this", "that", "here"]):
            # If living canvas or active app has a clear single target
            if visual_elements:
                primary_elem = visual_elements[0]
                return TargetReference(
                    target_id=primary_elem.id,
                    target_type=primary_elem.type.value if hasattr(primary_elem.type, "value") else str(primary_elem.type),
                    source=primary_elem.provenance,
                    confidence=primary_elem.confidence,
                    provenance=primary_elem.provenance,
                    bounds=primary_elem.bounds,
                    application_identity=app_name,
                    context_binding={"text": primary_elem.text}
                ), False, None

        # Fallback default target reference
        return TargetReference(
            target_id="active_workspace",
            target_type="WORKSPACE",
            source=ProvenanceTag.APPLICATION_ADAPTER,
            confidence=0.8,
            provenance=ProvenanceTag.APPLICATION_ADAPTER,
            application_identity=app_name
        ), False, None
