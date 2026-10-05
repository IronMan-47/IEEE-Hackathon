"""
JARVIS Python Agent Core — Centralized Configuration
"""

import os
from typing import Optional

class AgentConfig:
    def __init__(self):
        self.provider_name: str = os.getenv("JARVIS_LLM_PROVIDER", "mock").lower()
        self.gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY", None)
        self.model_name: str = os.getenv("JARVIS_LLM_MODEL", "gemini-1.5-flash")
        self.port: int = int(os.getenv("JARVIS_AGENT_PORT", "8765"))
        self.host: str = os.getenv("JARVIS_AGENT_HOST", "127.0.0.1")

    def is_mock(self) -> bool:
        return self.provider_name == "mock" or not self.gemini_api_key

config = AgentConfig()
