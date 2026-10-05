"""
JARVIS Python Agent Core — Phase 13 Visual Output Sanitizer
Sanitizes, validates, and normalizes raw visual model outputs.
Clamps coordinates and confidence scores, maps unknown taxonomy types, and enforces prompt injection defense.
Visual model output is strictly UNTRUSTED.
"""

from typing import Dict, Any, List, Optional
from agent.perception.types import PerceptionResult
from agent.perception.visual.models import (
    VisualContext, VisualElement, VisualRegion, BoundingBox,
    ConfidenceLevel, ProvenanceSource, VisualElementType, get_confidence_level
)
from agent.perception.visual.context_hash import compute_visual_context_hash
from agent.perception.visual.ocr import redact_sensitive_text
from agent.core.logging import logger

MAX_ELEMENTS_COUNT = 500
MAX_REGIONS_COUNT = 100


class VisualSanitizer:
    @staticmethod
    def sanitize(
        raw_data: Dict[str, Any],
        perception_result: Optional[PerceptionResult] = None,
        source: ProvenanceSource = ProvenanceSource.VISION_MODEL
    ) -> VisualContext:
        """
        Validates and sanitizes untrusted raw dictionary output into a safe, typed VisualContext.
        """
        if not isinstance(raw_data, dict):
            logger.warn("VisualSanitizer: Raw visual data is not a dict; returning fallback empty VisualContext")
            raw_data = {}

        # 1. Bounds Sanitization
        raw_bounds = raw_data.get("bounds", {}) if isinstance(raw_data.get("bounds"), dict) else {}
        def _safe_int(val, default=0):
            try:
                return max(0, int(val))
            except (ValueError, TypeError):
                return default

        default_w = perception_result.screen_metadata.active_width if perception_result else 1920
        default_h = perception_result.screen_metadata.active_height if perception_result else 1080

        context_bounds = BoundingBox(
            x=_safe_int(raw_bounds.get("x", 0)),
            y=_safe_int(raw_bounds.get("y", 0)),
            width=_safe_int(raw_bounds.get("width", default_w), default_w),
            height=_safe_int(raw_bounds.get("height", default_h), default_h)
        )

        # 2. Confidence Sanitization
        try:
            raw_conf = float(raw_data.get("confidence", 1.0))
        except (ValueError, TypeError):
            raw_conf = 1.0
        conf_score = max(0.0, min(1.0, raw_conf))
        conf_level = get_confidence_level(conf_score)

        # 3. Application Metadata
        app_name = str(raw_data.get("application", perception_result.active_application.name if perception_result else "Unknown"))
        app_class = str(raw_data.get("application_class", perception_result.classification.value if perception_result else "UNKNOWN"))

        # 4. Regions Sanitization
        raw_regions = raw_data.get("regions", [])
        if not isinstance(raw_regions, list):
            raw_regions = []
        raw_regions = raw_regions[:MAX_REGIONS_COUNT]

        sanitized_regions: List[VisualRegion] = []
        for idx, r in enumerate(raw_regions):
            if not isinstance(r, dict):
                continue
            r_bounds_raw = r.get("bounds", {})
            r_bounds = BoundingBox(
                x=max(0, int(r_bounds_raw.get("x", 0))),
                y=max(0, int(r_bounds_raw.get("y", 0))),
                width=max(0, int(r_bounds_raw.get("width", 100))),
                height=max(0, int(r_bounds_raw.get("height", 100)))
            )
            elem_ids = r.get("element_ids", [])
            if not isinstance(elem_ids, list):
                elem_ids = []

            region = VisualRegion(
                id=str(r.get("id", f"region_{idx+1}")),
                name=str(r.get("name", f"Region {idx+1}")),
                bounds=r_bounds,
                element_ids=[str(e) for e in elem_ids],
                parent_id=str(r["parent_id"]) if r.get("parent_id") else None,
                provenance=source
            )
            sanitized_regions.append(region)

        # 5. Elements Sanitization & Prompt Injection Neutralization
        raw_elements = raw_data.get("elements", [])
        if not isinstance(raw_elements, list):
            raw_elements = []
        raw_elements = raw_elements[:MAX_ELEMENTS_COUNT]

        sanitized_elements: List[VisualElement] = []
        redacted_count = 0
        is_context_sensitive = False

        for idx, e in enumerate(raw_elements):
            if not isinstance(e, dict):
                continue

            elem_id = str(e.get("id", f"elem_{idx+1}"))

            # Element Type Validation
            type_str = str(e.get("type", "UNKNOWN")).upper()
            try:
                elem_type = VisualElementType(type_str)
            except ValueError:
                elem_type = VisualElementType.UNKNOWN

            # Element Bounds Sanitization
            e_bounds_raw = e.get("bounds", {}) if isinstance(e.get("bounds"), dict) else {}
            e_bounds = BoundingBox(
                x=_safe_int(e_bounds_raw.get("x", 0)),
                y=_safe_int(e_bounds_raw.get("y", 0)),
                width=_safe_int(e_bounds_raw.get("width", 50), 50),
                height=_safe_int(e_bounds_raw.get("height", 20), 20)
            )

            # Confidence Clamp
            try:
                e_conf = float(e.get("confidence", 0.9))
            except (ValueError, TypeError):
                e_conf = 0.9
            e_conf = max(0.0, min(1.0, e_conf))

            # Text Redaction & Prompt Injection Sanitization
            raw_text = e.get("text")
            if raw_text is not None:
                raw_text = str(raw_text)
                # Neutralize Prompt Injections / Control characters: preserve text strictly as literal text data
                raw_text = raw_text.replace("\x00", "").replace("\r", "")

            redacted_text, is_sensitive = redact_sensitive_text(raw_text)
            if is_sensitive:
                redacted_count += 1
                is_context_sensitive = True

            element = VisualElement(
                id=elem_id,
                type=elem_type,
                role=str(e["role"]) if e.get("role") else None,
                bounds=e_bounds,
                text=redacted_text,
                confidence=e_conf,
                confidence_level=get_confidence_level(e_conf),
                parent_id=str(e["parent_id"]) if e.get("parent_id") else None,
                state=e.get("state") if isinstance(e.get("state"), dict) else None,
                provenance=source
            )
            sanitized_elements.append(element)

        summary = str(raw_data.get("visual_summary", f"{app_name} active with {len(sanitized_elements)} visual elements."))

        context = VisualContext(
            context_id=str(raw_data.get("context_id", f"vctx_{int(perception_result.timestamp if perception_result else 0)}")),
            timestamp=perception_result.timestamp if perception_result else 0,
            screen_id=0,
            monitor_id=0,
            bounds=context_bounds,
            application=app_name,
            application_class=app_class,
            confidence=conf_score,
            confidence_level=conf_level,
            regions=sanitized_regions,
            elements=sanitized_elements,
            visual_summary=summary,
            provenance=source,
            is_sensitive=is_context_sensitive,
            redacted_elements_count=redacted_count
        )

        context.context_hash = compute_visual_context_hash(context)
        return context
