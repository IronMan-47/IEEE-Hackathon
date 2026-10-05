import os

def fix_all_tokens():
    for r, d, files in os.walk('tests'):
        for f in files:
            if not f.endswith('.py'): continue
            path = os.path.join(r, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # Replace valid_approval_token dictionary with a function call
            # Wait, valid_approval_token is passed as a fixture. Let's make it a factory.
            if "def valid_approval_token(" in content:
                # Replace the whole fixture
                pass
                
    print("This might be complex. Let's just do a simpler regex.")
    
import re
def apply_regex():
    for r, d, files in os.walk('tests'):
        for f in files:
            if not f.endswith('.py'): continue
            path = os.path.join(r, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            original_content = content
            
            # Replace fixture valid_approval_token to be a factory
            fixture_code = \"\"\"@pytest.fixture
def valid_approval_token():
    from agent.execution.authorization import auth_service
    def _mint(proposal):
        return auth_service.generate_token(proposal)
    return _mint\"\"\"
            # Find the old fixture
            content = re.sub(r'@pytest\.fixture\s*def valid_approval_token\(\):\s*import uuid\s*return\s*\{[^}]+\}', fixture_code, content, flags=re.MULTILINE)
            
            # Replace valid_approval_token usage
            # Where we have `approval_token=valid_approval_token,` replace with `approval_token=valid_approval_token(proposal),`
            # Wait, `proposal` is sometimes defined AFTER?
            # Actually, `request = ExecutionRequest(..., approval_token=valid_approval_token)` comes after `proposal = Proposal(...)`.
            content = content.replace("approval_token=valid_approval_token,", "approval_token=valid_approval_token(proposal),")
            content = content.replace("approval_token=token,", "approval_token=auth_service.generate_token(proposal),")
            content = content.replace("approval_token=valid_approval_token\n", "approval_token=valid_approval_token(proposal)\n")
            
            # In test_execution_engine.py, it's defined as `token = {"tokenId": ...}`
            # Let's replace `token = {"tokenId": "tok_1", "proposalId": proposal.proposal_id, "baseRevision": 2, "contextHash": rel_ctx.context_hash}`
            # with `from agent.execution.authorization import auth_service; token = auth_service.generate_token(proposal)`
            content = re.sub(r'token = \{"tokenId": [^}]+\}', 'from agent.execution.authorization import auth_service\\n    token = auth_service.generate_token(proposal)', content)
            
            # test_jarvis_agent_orchestrated_browser_execution
            # valid_approval_token["contextHash"] = base_hash
            content = re.sub(r'valid_approval_token\["contextHash"\] = base_hash', '', content)
            content = re.sub(r'valid_approval_token\["proposalId"\] = "[^"]+"', '', content)
            content = re.sub(r'valid_approval_token\["tokenId"\] = "[^"]+"', '', content)
            
            if content != original_content:
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(content)

apply_regex()
