import os

def fix_tests():
    # 1. test_execution_engine.py
    path1 = "tests/python/test_execution_engine.py"
    with open(path1, "r", encoding="utf-8") as f:
        content = f.read()
    
    # We need to add `from agent.runtime.lifecycle import runtime_manager` and use it
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
    
    with open(path1, "w", encoding="utf-8") as f:
        f.write(content)

    # 2. test_vscode_executor.py
    path2 = "tests/python/test_vscode_executor.py"
    with open(path2, "r", encoding="utf-8") as f:
        content2 = f.read()

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
    content2 = content2.replace(old_code_2, new_code_2)

    with open(path2, "w", encoding="utf-8") as f:
        f.write(content2)

fix_tests()
