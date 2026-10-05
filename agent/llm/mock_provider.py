"""
JARVIS Python Agent Core — Mock LLM Provider
Deterministic proposal generation for testing without network or API key dependencies.
"""

import time
from typing import Dict, Any, Optional, Tuple
from agent.llm.provider import LLMProvider
from agent.context.workspace_context import WorkspaceContextModel

class MockProvider(LLMProvider):
    def generate_proposal(self, context: WorkspaceContextModel, user_text: str, plan: Optional[Any] = None) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        text_lower = user_text.lower()

        # Simulate provider failure test case if requested
        if "sim_fail" in text_lower or "trigger_error" in text_lower:
            return False, None, "Simulated LLM Provider Timeout / API Error"
            
        domain = context.raw.get("activeAppDomain", "living_canvas").lower()
        if domain not in ["living_canvas", "vscode", "browser", "terminal", "figma"]:
            domain = "living_canvas"


        if domain == "vscode":
            operations = [
                {
                    "op_type": "CODE_CHANGE",
                    "target": "active_file.py",
                    "parameters": {
                        "file": "active_file.py",
                        "target_content": "def add(a, b):",
                        "replacement_content": "def add(a, b):\\n    return a + b",
                        "old_text": "def add(a, b):",
                        "new_text": "def add(a, b):\\n    return a + b"
                    },
                    "reason": "Mock vscode code change"
                }
            ]
        elif domain == "browser":
            operations = [
                {
                    "op_type": "CLICK_ELEMENT",
                    "target": "button#test",
                    "parameters": {"target": "button#test", "role": "button", "origin": "https://example.com"},
                    "reason": "Mock browser click"
                }
            ]
        else:
            operations = [
                {
                    "op_type": "UPDATE_STYLE",
                    "target": "btn_pay",
                    "parameters": {
                        "w": 320,
                        "style": {
                            "fill": "#06B6D4",
                            "fontWeight": "bold"
                        }
                    },
                    "reason": "Enlarge Pay Now CTA button width (180px -> 320px) and apply cyan fill for visual prominence."
                }
            ]

        proposal_dict = {
            "id": f"prop_py_mock_{int(time.time() * 1000)}",
            "workspaceId": "checkout-demo",
            "baseRevision": context.revision,
            "title": "AI Proposal: Optimize Checkout CTA Hierarchy & Prominence",
            "reason": f"Analyzed workspace context for prompt '{user_text}'. Primary CTA 'btn_pay' currently has weak visual hierarchy (#475569) relative to surrounding elements.",
            "operations": operations,
            "createdAt": int(time.time() * 1000),
            "source": "AI",
            "status": "PENDING"
        }

        return True, proposal_dict, None

    def generate_plan(self, context: WorkspaceContextModel, user_text: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        return True, {
            "steps": [
                {"id": "step_1", "type": "OBSERVE", "description": "Observe workspace", "target_id": "active", "reason": "Gather context"},
                {"id": "step_2", "type": "PROPOSE", "description": "Generate proposal", "target_id": "active", "reason": "Draft changes"}
            ]
        }, None
