import re

target_file = r"c:\Users\lenovo\OneDrive\Desktop\Hackathons\Jarvis - Living Assistent\agent\proposals\sanitizer.py"
with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

# I will replace the sanitization logic to handle both dictionaries directly instead of Pydantic models.
new_sanitize = '''    @staticmethod
    def sanitize(proposal_dict: Dict[str, Any], known_element_ids: List[str]) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Sanitizes proposal payload against malicious inputs, prompt injection, and illegal operations.
        Handles both Phase 9 and Phase 15 formats.
        """
        operations = proposal_dict.get("operations", [])
        
        if len(operations) > MAX_OPS_PER_PROPOSAL:
            return False, None, f"Operation limit exceeded: Proposal contains {len(operations)} operations (Max allowed: {MAX_OPS_PER_PROPOSAL})"

        forbidden_patterns = [
            "<script>", "javascript:", "eval(", "exec(", "import ", "__import__",
            "system(", "passthru(", "shell_exec", "cmd.exe", "powershell",
            "ignore previous instructions", "override system prompt", "bypass safety"
        ]
        
        from agent.core.operations import ALL_KNOWN_OPS

        sanitized_ops = []
        for op in operations:
            op_type = op.get("op_type") or op.get("op")
            target = op.get("target") or op.get("targetId")
            params = op.get("parameters") or op.get("proposedValue") or {}
            reason = op.get("reason", "")
            
            if not op_type:
                return False, None, "Missing op_type"

            if op_type not in ALL_KNOWN_OPS:
                return False, None, f"Disallowed operation type: {op_type}"

            if op_type != "CREATE_ELEMENT" and target not in known_element_ids:
                return False, None, f"Operation targets unknown element ID: {target}"

            serialized = (str(params) + " " + reason).lower()
            for pattern in forbidden_patterns:
                if pattern in serialized:
                    return False, None, f"Security Violation: Forbidden injection pattern '{pattern}' detected"

            sanitized_ops.append(op)

        proposal_dict["operations"] = sanitized_ops
        return True, proposal_dict, None'''

content = re.sub(r'    @staticmethod\n    def sanitize.*?return True, clean_proposal, None', new_sanitize, content, flags=re.DOTALL)

with open(target_file, "w", encoding="utf-8") as f:
    f.write(content)
