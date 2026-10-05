"""
JARVIS Python Agent Core — Phase 14 Grounded Context Confidence Calculator
Calculates conservative context confidence based on source authority, agreement, freshness,
conflict severity, and target ambiguity.
"""

from typing import List, Optional
from agent.context.fusion.conflicts import ContextConflict, ConflictResolution
from agent.context.fusion.evidence import Evidence
from agent.context.fusion.provenance import get_provenance_precedence


class ContextConfidenceCalculator:
    @staticmethod
    def calculate_confidence(
        evidence_list: List[Evidence],
        conflicts: List[ContextConflict],
        target_ambiguous: bool = False
    ) -> float:
        """
        Calculates conservative grounded context confidence score (0.0 to 1.0).
        """
        if not evidence_list:
            return 0.5

        # Base confidence from evidence sources
        source_scores = [get_provenance_precedence(e.source) / 100.0 * e.confidence for e in evidence_list]
        avg_score = sum(source_scores) / len(source_scores)

        # Conflict Penalty
        unresolved_conflicts = [c for c in conflicts if c.resolution != ConflictResolution.AUTHORITATIVE_SOURCE]
        conflict_penalty = 0.25 * len(unresolved_conflicts)

        # Ambiguity Penalty
        ambiguity_penalty = 0.30 if target_ambiguous else 0.0

        final_conf = max(0.1, min(1.0, avg_score - conflict_penalty - ambiguity_penalty))
        return round(final_conf, 2)
