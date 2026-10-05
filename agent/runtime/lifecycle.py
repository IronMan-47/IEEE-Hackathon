import os
import threading
import time
from typing import Optional, Dict, Any

from agent.runtime.models import AgentRuntimeState, RuntimeStatus, RecoveryState, AgentEvent, RuntimeSnapshot
from agent.runtime.event_bus import EventBus
from agent.runtime.persistence import RuntimePersistence
from agent.runtime.recovery import ExecutionReconciler, ReconciliationOutcome
from agent.core.logging import logger

class AgentRuntimeManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AgentRuntimeManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.state = AgentRuntimeState()
        self.event_bus = EventBus()
        self.persistence = RuntimePersistence()
        self.lock = threading.RLock()
        
        self._heartbeat_thread = None
        self._running = False
        self._initialized = True

    def initialize(self):
        with self.lock:
            self.state.status = RuntimeStatus.STARTING
            logger.info(f"Runtime status: {RuntimeStatus.STARTING.value}")
            
            # 1. Load Snapshot
            try:
                snapshot = self.persistence.load_snapshot()
                if snapshot:
                    logger.info("Loaded previous runtime snapshot. Initiating recovery...")
                    self._transition(RuntimeStatus.RECOVERING)
                    self.state.runtime_id = snapshot.runtime_state.runtime_id
                    self.state.active_task_id = snapshot.runtime_state.active_task_id
                    self.state.active_context_id = snapshot.runtime_state.active_context_id
                    
                    # Check for execution uncertainty or pending approvals
                    if snapshot.runtime_state.active_execution_id:
                        self.state.recovery_state = RecoveryState.EXECUTION_UNCERTAIN
                        self.state.recovery_required = True
                    elif snapshot.approval_status and snapshot.approval_status.get("pending"):
                        self.state.recovery_state = RecoveryState.AUTHORIZATION_INVALIDATED
                        self.state.recovery_required = True
                    else:
                        self.state.recovery_state = RecoveryState.NONE
                else:
                    self.state.recovery_state = RecoveryState.NONE
            except Exception as e:
                logger.error(f"Failed to recover from snapshot: {e}")
                self.state.recovery_state = RecoveryState.RECOVERY_REQUIRED
                self.state.recovery_required = True
                # Enter a safe stopped state or waiting for human decision
                self._transition(RuntimeStatus.WAITING_FOR_HUMAN)
            
            # Emit RUNTIME_READY
            if self.state.recovery_required:
                self._emit("RUNTIME_READY", {"recovery_required": True})
            else:
                self._transition(RuntimeStatus.READY)
                self._emit("RUNTIME_READY", {"recovery_required": False})
                self._transition(RuntimeStatus.RUNNING)

    def shutdown(self):
        with self.lock:
            self._transition(RuntimeStatus.SHUTTING_DOWN)
            self._emit("RUNTIME_SHUTTING_DOWN", {})
            self._save_snapshot()
            self._running = False
            self._transition(RuntimeStatus.STOPPED)
            self._emit("RUNTIME_STOPPED", {})

    def trigger_emergency_stop(self):
        with self.lock:
            self.state.emergency_stop_state = True
            self._transition(RuntimeStatus.SAFE_STOPPED)
            self._emit("EMERGENCY_STOP_ACTIVATED", {})

    def clear_emergency_stop(self):
        with self.lock:
            self.state.emergency_stop_state = False
            self._transition(RuntimeStatus.RUNNING)
            self._emit("EMERGENCY_STOP_CLEARED", {})

    def handle_heartbeat(self, payload: Dict[str, Any]):
        with self.lock:
            self.state.electron_connection_status = "CONNECTED"
            self._emit("ELECTRON_CONNECTED", payload)

    def reconcile_execution(self, domain: str, proposal: Dict[str, Any], exec_req: Dict[str, Any], ctx: Dict[str, Any]):
        with self.lock:
            outcome = ExecutionReconciler.reconcile(domain, proposal, exec_req, ctx)
            self._emit("RECOVERY_RECONCILIATION_COMPLETED", {"outcome": outcome.value})
            
            if outcome == ReconciliationOutcome.UNKNOWN:
                self.state.recovery_state = RecoveryState.HUMAN_DECISION_REQUIRED
                self._transition(RuntimeStatus.WAITING_FOR_HUMAN)
            else:
                self.state.recovery_state = RecoveryState.NONE
                self.state.recovery_required = False
                self._transition(RuntimeStatus.RUNNING)

    def _transition(self, new_status: RuntimeStatus):
        # State Machine Transitions
        # Basic validation could go here
        old_status = self.state.status
        self.state.status = new_status
        logger.info(f"Runtime transitioned: {old_status.value} -> {new_status.value}")
        self._save_snapshot()

    def _emit(self, event_type: str, payload: Dict[str, Any]):
        evt = AgentEvent(
            event_type=event_type,
            runtime_id=self.state.runtime_id,
            payload=payload,
            task_id=self.state.active_task_id
        )
        self.event_bus.publish(evt)

    def _save_snapshot(self):
        snap = RuntimeSnapshot(
            runtime_state=self.state,
            last_event_sequence=self.event_bus._sequence_counter
        )
        self.persistence.save_snapshot(snap)

runtime_manager = AgentRuntimeManager()
