"""
JARVIS Python Agent Core — Proposal Schema Definitions
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from agent.core.operations import LIVING_CANVAS_OPS as ALLOWED_PATCH_OPS

class PatchOperationSchema(BaseModel):
    op: str
    targetId: str
    proposedValue: Dict[str, Any] = Field(default_factory=dict)
    reason: str

class ProposalSchema(BaseModel):
    id: str
    workspaceId: str
    baseRevision: int
    title: str
    reason: str
    operations: List[PatchOperationSchema]
    createdAt: int
    source: str = "AI"
    status: str = "PENDING"
