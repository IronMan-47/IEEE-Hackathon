"""
JARVIS Python Agent Core — Phase 13 Visual Context Hashing & Staleness Detection
Computes canonical SHA-256 visual context hash based on normalized semantic elements and regions.
Provides staleness detection to prevent stale visual perception from being used in reasoning.
"""

import json
import time
import hashlib
from typing import Optional, Tuple, Dict, Any
from agent.perception.visual.models import VisualContext


def compute_visual_context_hash(context: VisualContext) -> str:
    """
    Computes a canonical SHA-256 hash of the normalized semantic visual context.
    Omits volatile fields like timestamps or raw object memory references.
    """
    canonical_regions = []
    for r in sorted(context.regions, key=lambda x: x.id):
        canonical_regions.append({
            "id": r.id,
            "name": r.name,
            "bounds": {"x": r.bounds.x, "y": r.bounds.y, "w": r.bounds.width, "h": r.bounds.height},
            "elements": sorted(r.element_ids)
        })

    canonical_elements = []
    for e in sorted(context.elements, key=lambda x: x.id):
        canonical_elements.append({
            "id": e.id,
            "type": e.type.value if hasattr(e.type, "value") else str(e.type),
            "role": e.role or "",
            "bounds": {"x": e.bounds.x, "y": e.bounds.y, "w": e.bounds.width, "h": e.bounds.height},
            "text": e.text or "",
            "parent_id": e.parent_id or ""
        })

    canonical_data: Dict[str, Any] = {
        "application": context.application,
        "application_class": context.application_class,
        "bounds": {
            "x": context.bounds.x,
            "y": context.bounds.y,
            "w": context.bounds.width,
            "h": context.bounds.height
        },
        "regions": canonical_regions,
        "elements": canonical_elements
    }

    serialized = json.dumps(canonical_data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def is_visual_context_stale(
    context: VisualContext,
    current_context: Optional[VisualContext] = None,
    max_age_ms: int = 30000,
    current_time_ms: Optional[int] = None
) -> Tuple[bool, str]:
    """
    Determines if a visual context is stale due to age expiration or context hash divergence.
    Returns (is_stale, reason_string).
    """
    now = current_time_ms if current_time_ms is not None else int(time.time() * 1000)
    age = now - context.timestamp

    if age > max_age_ms:
        return True, f"VISUAL_CONTEXT_EXPIRED: Perception age ({age}ms) exceeds max age ({max_age_ms}ms)"

    if current_context is not None:
        fresh_hash = compute_visual_context_hash(current_context)
        if context.context_hash and context.context_hash != fresh_hash:
            return True, f"VISUAL_CONTEXT_DIVERGED: Context hash mismatch ({context.context_hash[:8]} != {fresh_hash[:8]})"

    return False, "VISUAL_CONTEXT_FRESH"
