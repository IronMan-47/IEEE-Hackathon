"""
JARVIS Python Agent Core — Domain Executor Abstract Base Class
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any
from agent.execution.models import ExecutionRequest, ExecutionResult
from agent.proposals.models import Proposal
from agent.context.relevance_filter import RelevantContext


class BaseDomainExecutor(ABC):
    @abstractmethod
    def can_execute(self, domain: str) -> bool:
        """Returns True if this executor supports the specified domain."""
        pass

    @abstractmethod
    def execute(
        self,
        request: ExecutionRequest,
        proposal: Proposal,
        context: RelevantContext,
        workspace_context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """Safely executes the approved proposal against the target domain."""
        pass
