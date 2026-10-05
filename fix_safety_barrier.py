import os

def fix_safety_barrier():
    path = 'agent/execution/safety_barrier.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    start_str = '# 3. Approval Token Validation'
    end_str = 'return False, "Token proposal ID mismatch", res'
    i = content.find(start_str)
    j = content.find(end_str, i) + len(end_str)
    
    if i != -1 and j > i:
        new_code = """# 3. Approval Token Validation
        from agent.execution.authorization import auth_service
        # Token validation checks signature, replay, expiration, and proposal bindings
        if not auth_service.verify_token(request.approval_token, request):
            res = cls._build_blocked_result(request, "UNAUTHORIZED: Missing, expired, mismatched or malformed ApprovalToken")
            return False, "Invalid ApprovalToken", res"""
        content = content[:i] + new_code + content[j:]
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated safety_barrier.py verification")

    # Also update consume_token_atomically
    start_str_consume = 'def consume_token_atomically(cls, token_id: str) -> bool:'
    end_str_consume = 'return True'
    i = content.find(start_str_consume)
    j = content.find(end_str_consume, i) + len(end_str_consume)
    if i != -1 and j > i:
        new_consume = """def consume_token_atomically(cls, token_id: str) -> bool:
        \"\"\"Atomically marks an ApprovalToken as consumed to prevent replay attacks.\"\"\"
        from agent.execution.authorization import auth_service
        return auth_service.consume_token(token_id)"""
        content = content[:i] + new_consume + content[j:]
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated consume_token_atomically")

fix_safety_barrier()
