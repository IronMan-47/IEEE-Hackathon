import { OverlayView, OverlayState } from './components/overlay-view.js';

// Immediately invoked setup since the script is at the end of the body
async function initRenderer() {
  const container = document.getElementById('jarvis-overlay-container');
  if (!container) return;

  const api = (window as any).jarvisAPI;
  if (!api) {
    console.error('JARVIS Electron API not found');
    container.innerHTML = '<div style="background:var(--bg-primary); padding: 20px; border:1px solid var(--danger); border-radius:12px; color:white; width: 320px;"><strong>CRITICAL ERROR:</strong><br/>Electron Preload API (jarvisAPI) not found. The preload script may have crashed.</div>';
    return;
  }

  let currentState: OverlayState = {
    runtimeState: 'CONNECTING',
    isExpanded: false,
    activeApp: 'Unknown',
    isMicActive: false,
    isScreenActive: false
  };

  const overlay = new OverlayView('jarvis-overlay-container', {
    onToggleExpand: () => {
      currentState.isExpanded = !currentState.isExpanded;
      overlay.updateState(currentState);
    },
    onSubmitCommand: async (text: string) => {
      try {
        await api.createTask(text);
      } catch (e) {
        console.error(e);
      }
    },
    onEmergencyStop: async () => {
      await api.requestEmergencyStop();
    },
    onApproveProposal: async () => {
      if (currentState.activeTask) {
        const step = currentState.activeTask.steps[currentState.activeTask.current_step_index];
        await api.approveTaskStep(currentState.activeTask.task_id, step.step_id);
        // also execute immediately for demo purposes
        await api.executeTaskStep(currentState.activeTask.task_id, step.step_id);
      }
    },
    onRejectProposal: async () => {
      if (currentState.activeTask) {
        await api.cancelTask(currentState.activeTask.task_id);
      }
    },
    onToggleMic: async () => {
      if (currentState.isMicActive) {
        await api.stopVoiceListening();
        currentState.isMicActive = false;
      } else {
        await api.startVoiceListening();
        currentState.isMicActive = true;
      }
      overlay.updateState(currentState);
    }
  });

  async function syncState() {
    try {
      const rtState = await api.getRuntimeState();
      
      // Attempt to get active task if any
      let activeTask = null;
      let currentProposal = null;
      
      if (rtState.active_task_id) {
        try {
          const taskRes = await api.getTask(rtState.active_task_id);
          if (taskRes && taskRes.task_id) {
            activeTask = taskRes;
            const currentStep = activeTask.steps[activeTask.current_step_index];
            if (currentStep && currentStep.proposal && currentStep.status === 'AWAITING_APPROVAL') {
              currentProposal = currentStep.proposal;
            }
          }
        } catch(e) {}
      }

      // Dynamic active app detection via perception API
      let activeApp = 'Desktop';
      if (activeTask && activeTask.grounded_context && activeTask.grounded_context.primary_application) {
          activeApp = activeTask.grounded_context.primary_application.name;
      } else {
          try {
              const pContext = await api.getApplicationContext();
              if (pContext && pContext.application_context && pContext.application_context.name) {
                  const fetchedApp = pContext.application_context.name;
                  // BUG #2: Preserve previous user foreground app; do NOT overwrite with JARVIS itself
                  if (!fetchedApp.toLowerCase().includes('jarvis') && !fetchedApp.toLowerCase().includes('electron')) {
                      activeApp = fetchedApp;
                  }
              }
          } catch (e) {
              // Ignore perception errors, retain previous activeApp
          }
      }

      currentState = {
        ...currentState,
        runtimeState: rtState.status,
        activeApp: activeApp,
        recoveryState: rtState.recovery_state,
        activeTask,
        currentProposal
      };

      overlay.updateState(currentState);
    } catch (err) {
      console.error('State sync failed:', err);
      currentState.runtimeState = 'DISCONNECTED';
      overlay.updateState(currentState);
    }
  }

  // Handle IPC Status changes (Phase 17 EventBus -> IPC)
  api.onStatusChanged((payload: any) => {
    if (payload.state === 'STOPPED') {
      currentState.runtimeState = 'SAFE_STOPPED';
    }
    syncState();
  });

  // Setup Hotkey receiver mock
  window.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.shiftKey && e.code === 'Space') {
      // Focus overlay input and expand
      currentState.isExpanded = true;
      overlay.updateState(currentState);
      const input = document.getElementById('cmd-input');
      if (input) input.focus();
    }
  });

  // Initial Sync
  await syncState();
  
  // Polling fallback to keep UI fresh since we removed complex IPC websocket setup
  setInterval(syncState, 2000);
}

// Start the app
initRenderer().catch(console.error);
