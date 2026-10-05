"""
JARVIS Python Agent Core — Phase 14 Fused Relevance Engine
Filters grounded context facts, evidence, and visual elements based on user query intent.
"""

from typing import Optional
from agent.context.fusion.models import GroundedContext


class FusedRelevanceEngine:
    @staticmethod
    def filter_grounded_context(
        grounded_context: GroundedContext,
        user_query: Optional[str] = None,
        max_evidence: int = 15
    ) -> GroundedContext:
        """
        Returns a copy of GroundedContext with evidence and facts filtered for relevance.
        """
        if not user_query:
            return grounded_context

        q_lower = user_query.lower().strip()
        keywords = [w for w in q_lower.split() if len(w) > 2]

        # Filter evidence items
        scored_evidence = []
        for ev in grounded_context.evidence_list:
            score = ev.confidence
            ref_lower = ev.content_reference.lower()
            for kw in keywords:
                if kw in ref_lower:
                    score += 2.0
            scored_evidence.append((score, ev))

        scored_evidence.sort(key=lambda x: x[0], reverse=True)
        filtered_evidence = [item[1] for item in scored_evidence[:max_evidence]]

        ctx_copy = grounded_context.model_copy()
        ctx_copy.evidence_list = filtered_evidence
        return ctx_copy
