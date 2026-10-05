"""
JARVIS Python Agent Core — Phase 14 Grounded Context Hashing & Staleness
Computes canonical SHA-256 hash of normalized grounded context and checks staleness.
"""

import json
import time
import hashlib
from typing import Optional, Tuple, Dict, Any
from agent.context.fusion.models import GroundedContext


def compute_grounded_context_hash(context: GroundedContext) -> str:
    """
    Computes a canonical SHA-256 hash of normalized grounded context.
    Omits volatile timestamps to ensure deterministic hashing.
    """
    canonical_facts = []
    for f in sorted(context.facts, key=lambda x: x.id):
        canonical_facts.append({
            "id": f.id,
            "statement": f.statement,
            "type": f.type.value if hasattr(f.type, "value") else str(f.type),
            "provenance": f.provenance.value if hasattr(f.provenance, "value") else str(f.provenance)
        })

    canonical_evidence = []
    for e in sorted(context.evidence_list, key=lambda x: x.evidence_id):
        canonical_evidence.append({
            "id": e.evidence_id,
            "type": e.type.value if hasattr(e.type, "value") else str(e.type),
            "source": e.source.value if hasattr(e.source, "value") else str(e.source),
            "content": e.content_reference
        })

    target_data = {}
    if context.active_target:
        t = context.active_target
        target_data = {
            "target_id": getattr(t, "target_id", ""),
            "target_type": getattr(t, "target_type", ""),
            "is_ambiguous": getattr(t, "is_ambiguous", False)
        }

    canonical_data: Dict[str, Any] = {
        "primary_app": context.primary_application.name,
        "primary_process": context.primary_application.process_name,
        "secondary_apps": [a.name for a in context.secondary_applications],
        "application_context": {
            "active_file": context.application_context.get("active_file") or context.application_context.get("file"),
            "origin": context.application_context.get("origin") or context.application_context.get("active_url")
        },
        "target": target_data,
        "facts": canonical_facts,
        "evidence": canonical_evidence
    }

    serialized = json.dumps(canonical_data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def is_grounded_context_stale(
    context: GroundedContext,
    current_context: Optional[GroundedContext] = None,
    max_age_ms: int = 30000,
    current_time_ms: Optional[int] = None
) -> Tuple[bool, str]:
    """
    Determines if grounded context is stale due to age expiration or context hash divergence.
    """
    now = current_time_ms if current_time_ms is not None else int(time.time() * 1000)
    age = now - context.timestamp

    if age > max_age_ms:
        return True, f"GROUNDED_CONTEXT_EXPIRED: Context age ({age}ms) exceeds max age ({max_age_ms}ms)"

    if current_context is not None:
        fresh_hash = compute_grounded_context_hash(current_context)
        if context.context_hash and context.context_hash != fresh_hash:
            return True, f"GROUNDED_CONTEXT_DIVERGED: Hash mismatch ({context.context_hash[:8]} != {fresh_hash[:8]})"

    return False, "GROUNDED_CONTEXT_FRESH"
