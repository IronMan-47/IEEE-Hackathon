import os

def fix_tests_safely():
    for root, _, files in os.walk('tests/python'):
        for file in files:
            if not file.endswith('.py'): continue
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            original = content

            if "from agent.execution.authorization import auth_service" not in content:
                content = "from agent.execution.authorization import auth_service\n" + content

            content = content.replace('approval_token=valid_approval_token,', 'approval_token=auth_service.generate_token(proposal),')
            content = content.replace('approval_token=valid_approval_token\n', 'approval_token=auth_service.generate_token(proposal)\n')
            content = content.replace('approval_token=valid_approval_token)', 'approval_token=auth_service.generate_token(proposal))')
            
            # test_execution_engine.py specific fixes
            content = content.replace(
                'token = {"tokenId": "tok_1", "proposalId": proposal.proposal_id, "baseRevision": 2, "contextHash": rel_ctx.context_hash}',
                'token = auth_service.generate_token(proposal)'
            )
            content = content.replace('approval_token=token,', 'approval_token=auth_service.generate_token(proposal),')
            
            # remove test_jarvis_agent_orchestrated_browser_execution dictionary modifications
            content = content.replace('valid_approval_token["contextHash"] = base_hash', '')
            content = content.replace('valid_approval_token["proposalId"] = "prop_browser_agent"', '')
            content = content.replace('valid_approval_token["tokenId"] = "token_browser_agent_1"', '')
            
            content = content.replace('valid_approval_token["proposalId"] = "prop_vscode_agent"', '')
            content = content.replace('valid_approval_token["tokenId"] = "token_vscode_agent_1"', '')

            # is_system_ready=True removals
            content = content.replace(', is_system_ready=True', '')
            content = content.replace('is_system_ready=True', '')

            # is_system_ready=False removals
            old_code_1 = """    executor = LivingCanvasExecutor()
    res = executor.execute(exec_req, proposal, rel_ctx, workspace_context={"revision": 2}, is_system_ready=False)"""
    
            new_code_1 = """    executor = LivingCanvasExecutor()
    from agent.runtime.lifecycle import runtime_manager
    runtime_manager.state.emergency_stop_state = True
    try:
        res = executor.execute(exec_req, proposal, rel_ctx, workspace_context={"revision": 2})
    finally:
        runtime_manager.state.emergency_stop_state = False"""
            content = content.replace(old_code_1, new_code_1)

            old_code_2 = """    executor = VSCodeExecutor()
    # Pass is_system_ready=False to simulate active Emergency Stop
    result = executor.execute(
        request, proposal, mock_vscode_context,
        workspace_context={"allow_mock_app": True, "mock_files": {"example.py": initial_code}},
        is_system_ready=False
    )"""
            new_code_2 = """    executor = VSCodeExecutor()
    from agent.runtime.lifecycle import runtime_manager
    runtime_manager.state.emergency_stop_state = True
    try:
        result = executor.execute(
            request, proposal, mock_vscode_context,
            workspace_context={"allow_mock_app": True, "mock_files": {"example.py": initial_code}}
        )
    finally:
        runtime_manager.state.emergency_stop_state = False"""
            content = content.replace(old_code_2, new_code_2)
            
            if content != original:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Fixed {path}")

fix_tests_safely()
