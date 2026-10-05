"""
JARVIS Python Agent Core — Phase 13 Vision Provider Abstract Interface
Defines the contract for visual screen perception providers (Mock, Gemini, Local).
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from agent.perception.types import PerceptionResult
from agent.perception.visual.models import VisualContext


class VisionProvider(ABC):
    @abstractmethod
    def analyze_screen(
        self,
        perception_result: PerceptionResult,
        image_bytes: Optional[bytes] = None,
        scenario: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> VisualContext:
        """
        Analyzes screen capture and perception metadata to produce a structured VisualContext.
        """
        pass
