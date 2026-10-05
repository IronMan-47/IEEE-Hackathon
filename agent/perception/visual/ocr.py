"""
JARVIS Python Agent Core — Phase 13 Bounded OCR Engine & Privacy Text Redaction
Provides structured OCR extraction with bounding box preservation, whitespace normalization,
and sensitive keyword redaction (passwords, OTPs, CVVs, card numbers, API tokens).
"""

import re
from typing import List, Tuple, Optional, Dict, Any
from agent.perception.types import PerceptionResult
from agent.perception.visual.models import (
    VisualElement, VisualElementType, BoundingBox,
    ConfidenceLevel, ProvenanceSource, get_confidence_level
)

SENSITIVE_TEXT_KEYWORDS = {
    "password", "current-password", "new-password", "one-time-code", "otp",
    "cvv", "card-number", "credit-card", "credit card", "credit_card", "debit-card",
    "security-code", "pin", "ssn", "bearer", "api_key", "apikey", "secret_key", "private_key", "token"
}


def redact_sensitive_text(text: Optional[str]) -> Tuple[Optional[str], bool]:
    if not text:
        return text, False

    norm_text = text.strip()
    lowered = norm_text.lower()

    for kw in SENSITIVE_TEXT_KEYWORDS:
        if kw in lowered:
            return f"[REDACTED_SENSITIVE_{kw.upper().replace('-', '_')}]", True

    return norm_text, False


class OCREngine:
    @staticmethod
    def extract_text(
        perception_result: PerceptionResult,
        image_bytes: Optional[bytes] = None,
        raw_ocr_blocks: Optional[List[Dict[str, Any]]] = None
    ) -> List[VisualElement]:
        """
        Extracts OCR visual elements with bounding box preservation and redaction.
        If raw_ocr_blocks is provided, parses them; otherwise generates deterministic mock OCR blocks
        based on active application metadata to preserve reproducible testing.
        """
        elements: List[VisualElement] = []

        if raw_ocr_blocks is not None:
            blocks = raw_ocr_blocks
        else:
            blocks = OCREngine._generate_mock_ocr_blocks(perception_result)

        for idx, block in enumerate(blocks):
            raw_text = block.get("text", "")
            confidence = float(block.get("confidence", 0.95))
            confidence = max(0.0, min(1.0, confidence))

            redacted_text, is_sensitive = redact_sensitive_text(raw_text)

            box_dict = block.get("bounds", {})
            bounds = BoundingBox(
                x=max(0, int(box_dict.get("x", 0))),
                y=max(0, int(box_dict.get("y", 0))),
                width=max(0, int(box_dict.get("width", 100))),
                height=max(0, int(box_dict.get("height", 20)))
            )

            elem_type_str = block.get("type", "TEXT")
            try:
                elem_type = VisualElementType(elem_type_str.upper())
            except ValueError:
                elem_type = VisualElementType.TEXT

            element = VisualElement(
                id=f"ocr_elem_{idx+1}",
                type=elem_type,
                role=block.get("role", "text"),
                bounds=bounds,
                text=redacted_text,
                confidence=confidence,
                confidence_level=get_confidence_level(confidence),
                provenance=ProvenanceSource.OCR,
                state={"is_sensitive": is_sensitive}
            )
            elements.append(element)

        return elements

    @staticmethod
    def _generate_mock_ocr_blocks(perception_result: PerceptionResult) -> List[Dict[str, Any]]:
        app_name = perception_result.active_application.name.lower()
        win_title = perception_result.active_window.title

        if "code" in app_name or "vs code" in win_title.lower():
            return [
                {"text": win_title, "bounds": {"x": 10, "y": 10, "width": 400, "height": 30}, "type": "HEADING"},
                {"text": "def process_data(req):", "bounds": {"x": 50, "y": 100, "width": 300, "height": 25}, "type": "CODE_REGION"},
                {"text": "    return {'status': 'ok'}", "bounds": {"x": 50, "y": 130, "width": 300, "height": 25}, "type": "CODE_REGION"},
                {"text": "Terminal: python -m pytest", "bounds": {"x": 50, "y": 500, "width": 400, "height": 30}, "type": "TEXT"}
            ]
        elif "chrome" in app_name or "browser" in win_title.lower():
            return [
                {"text": win_title, "bounds": {"x": 0, "y": 0, "width": 800, "height": 40}, "type": "HEADING"},
                {"text": "Search or enter web address", "bounds": {"x": 100, "y": 50, "width": 500, "height": 30}, "type": "INPUT"},
                {"text": "Documentation Overview", "bounds": {"x": 100, "y": 150, "width": 350, "height": 40}, "type": "HEADING"}
            ]
        else:
            return [
                {"text": win_title or "Active Window", "bounds": {"x": 0, "y": 0, "width": 500, "height": 30}, "type": "HEADING"}
            ]
