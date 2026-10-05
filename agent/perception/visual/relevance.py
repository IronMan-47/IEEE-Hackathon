"""
JARVIS Python Agent Core — Phase 13 Visual Context Relevance Filter
Filters visual context elements based on user request intent, active application, and target region.
Keeps visual context compact for downstream planning and reasoning.
"""

from typing import List, Optional
from agent.perception.visual.models import VisualContext, VisualElement, VisualElementType


class VisualRelevanceFilter:
    @staticmethod
    def filter_context(
        context: VisualContext,
        user_query: Optional[str] = None,
        max_elements: int = 25
    ) -> VisualContext:
        """
        Returns a copy of VisualContext with elements filtered for relevance to the user request.
        """
        if not user_query:
            filtered_elements = context.elements[:max_elements]
        else:
            q_lower = user_query.lower()
            keywords = [w for w in q_lower.split() if len(w) > 2]

            scored_elements = []
            for elem in context.elements:
                score = 0.0
                elem_text = (elem.text or "").lower()
                elem_role = (elem.role or "").lower()
                elem_type = (elem.type.value if hasattr(elem.type, "value") else str(elem.type)).lower()

                for kw in keywords:
                    if kw in elem_text:
                        score += 3.0
                    if kw in elem_role or kw in elem_type:
                        score += 2.0

                # High confidence elements get boost
                score += elem.confidence

                scored_elements.append((score, elem))

            scored_elements.sort(key=lambda x: x[0], reverse=True)
            filtered_elements = [item[1] for item in scored_elements[:max_elements]]

        new_ctx = context.model_copy()
        new_ctx.elements = filtered_elements
        return new_ctx
