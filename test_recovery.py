import os
from agent.runtime.lifecycle import runtime_manager, AgentRuntimeState, RuntimeStatus, RecoveryState
from agent.runtime.persistence import RuntimePersistence
from agent.runtime.models import RuntimeSnapshot

def test_recovery():
    # Write a broken snapshot
    p = RuntimePersistence()
    
    with open(p.snapshot_file, "w") as f:
        f.write('{"timestamp": "2026", "runtime_state": {')
    
    runtime_manager._initialized = False
    runtime_manager.initialize()
    
    assert runtime_manager.state.recovery_required == True
    assert runtime_manager.state.recovery_state == RecoveryState.RECOVERY_REQUIRED
    assert runtime_manager.state.status == RuntimeStatus.WAITING_FOR_HUMAN
    
    print("Test passed: corrupted snapshot gracefully triggers RECOVERY_REQUIRED")
    
if __name__ == "__main__":
    test_recovery()
