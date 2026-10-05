"""
JARVIS Python Agent Core — Proposal Generator
"""

from typing import Dict, Any, Tuple, Optional
from agent.llm.provider import LLMProvider
from agent.llm.mock_provider import MockProvider
from agent.llm.gemini_provider import GeminiProvider
from agent.context.workspace_context import WorkspaceContextModel
from agent.core.config import config

class ProposalGenerator:
    def __init__(self, provider: Optional[LLMProvider] = None):
        if provider:
            self.provider = provider
        elif config.is_mock():
            self.provider = MockProvider()
        else:
            self.provider = GeminiProvider(api_key=config.gemini_api_key, model_name=config.model_name)

    def generate(self, context: WorkspaceContextModel, user_text: str, plan: Optional[Any] = None) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        return self.provider.generate_proposal(context, user_text, plan)
