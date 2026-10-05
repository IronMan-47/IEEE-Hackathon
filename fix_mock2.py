import re

target_file = r"c:\Users\lenovo\OneDrive\Desktop\Hackathons\Jarvis - Living Assistent\agent\llm\mock_provider.py"
with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

new_generate_proposal = '''    def generate_proposal(self, context: WorkspaceContextModel, user_text: str, plan: Optional[Any] = None) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        text_lower = user_text.lower()

        # Simulate provider failure test case if requested
        if "sim_fail" in text_lower or "trigger_error" in text_lower:
            return False, None, "Simulated LLM Provider Timeout / API Error"
            
        domain = "living_canvas"
        if plan:
            domain = getattr(plan, "domain", "living_canvas")
            # If not in plan directly, it might be derived elsewhere. We can guess by prompt.
        if "vscode" in text_lower or "format" in text_lower or "rename" in text_lower or "file" in text_lower or "code" in text_lower:
            domain = "vscode"
        if "browser" in text_lower or "navigate" in text_lower or "search" in text_lower or "click" in text_lower:
            domain = "browser"

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

        return True, proposal_dict, None'''

content = re.sub(r'    def generate_proposal.*?return True, proposal_dict, None', new_generate_proposal, content, flags=re.DOTALL)

with open(target_file, "w", encoding="utf-8") as f:
    f.write(content)
