"""
JARVIS Python Agent Core — Core Types & Data Models
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from agent.intent.models import IntentCategory


class AgentRequest(BaseModel):
    request_id: str = Field(..., description="Unique request tracking ID")
    text: str = Field(..., description="Natural language user request")
    workspace_context: Dict[str, Any] = Field(..., description="Structured workspace state")


class CandidateAction(BaseModel):
    op: str
    target_id: str
    proposed_value: Dict[str, Any]
    reason: str


class Plan(BaseModel):
    intent: IntentCategory
    explanation: str
    candidate_actions: List[CandidateAction] = []


class AgentResponse(BaseModel):
    request_id: str
    status: str  # "SUCCESS" | "UNSUPPORTED" | "ERROR"
    intent: IntentCategory
    proposal: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    error: Optional[str] = None
