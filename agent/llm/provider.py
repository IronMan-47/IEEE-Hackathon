"""
JARVIS Python Agent Core — LLM Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from agent.context.workspace_context import WorkspaceContextModel

class LLMProvider(ABC):
    @abstractmethod
    def generate_proposal(self, context: WorkspaceContextModel, user_text: str, plan: Optional[Any] = None) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Generates a structured proposal dictionary matching ProposalSchema.
        Returns (success, proposal_dict, error_message).
        """
        pass

    @abstractmethod
    def generate_plan(self, context: WorkspaceContextModel, user_text: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Generates a structured plan dictionary.
        Returns (success, plan_dict, error_message).
        """
        pass
