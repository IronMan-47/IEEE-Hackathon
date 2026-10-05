"""
JARVIS Phase 14 Context Fusion & Grounded Multimodal Reasoning Package
"""
from agent.context.fusion.provenance import ProvenanceTag
from agent.context.fusion.evidence import Evidence, EvidenceType
from agent.context.fusion.conflicts import ContextConflict, ConflictType, ConflictResolution
from agent.context.fusion.models import GroundedContext, FactStatement, FactType, ApplicationRole, AppInfo
from agent.context.fusion.target_resolution import TargetReference, TargetResolver
from agent.context.fusion.resolver import ContextResolver
from agent.context.fusion.confidence import ContextConfidenceCalculator
from agent.context.fusion.hash import compute_grounded_context_hash, is_grounded_context_stale
from agent.context.fusion.relevance import FusedRelevanceEngine

__all__ = [
    "ProvenanceTag", "Evidence", "EvidenceType", "ContextConflict", "ConflictType",
    "ConflictResolution", "GroundedContext", "FactStatement", "FactType",
    "ApplicationRole", "AppInfo", "TargetReference", "TargetResolver",
    "ContextResolver", "ContextConfidenceCalculator", "compute_grounded_context_hash",
    "is_grounded_context_stale", "FusedRelevanceEngine"
]
