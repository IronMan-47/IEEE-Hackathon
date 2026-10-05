# JARVIS Demo Recovery Guide

If something goes wrong during a live presentation, follow these exact deterministic steps to recover the state safely.

## 1. Python Runtime Crash (e.g. Out of Memory)
**Symptom**: The overlay UI shows `DISCONNECTED` or stops updating completely.
**Recovery**:
1. Open the terminal running `npm start`.
2. Press `Ctrl+C` to kill the process.
3. Rerun `npm start`.
4. The AgentRuntime will boot and read the last `EventBus` checkpoint.
5. The overlay will display `RECOVERY REQUIRED` (EXECUTION_UNCERTAIN).
6. Click "Cancel Task" to clear the queue, reset `main.py` manually if needed, and restart the demo.

## 2. Emergency Stop Triggered
**Symptom**: Presenter accidentally hits `Ctrl+Shift+F12`. UI shows `SAFE_STOPPED`.
**Recovery**:
1. Explain to the judges: "The emergency hardware kill-switch was hit, cutting all execution authority."
2. The UI will explicitly block input.
3. Click the Reactivate button (or restart the app) to resume normal operation.

## 3. Stale Proposal Error
**Symptom**: You click "Approve & Execute" but JARVIS rejects it.
**Recovery**:
1. Explain: "I accidentally changed the document while JARVIS was waiting. JARVIS's Execution Safety Barrier correctly identified a hash mismatch and prevented the execution."
2. Reject the blocked proposal in the UI.
3. Re-prompt JARVIS to generate a fresh, mathematically sound proposal based on the new document state.

## 4. Wrong Application Mismatch
**Symptom**: JARVIS expects the Browser but the presenter opens something else.
**Recovery**:
1. Explain: "JARVIS detected that I did not provide the required application context and safely halted the handoff."
2. Cancel the blocked task.
3. Ensure the browser is the active window for the correct step on the next run.

## Demo Reset Procedure (Post-Demo)
To prepare for the next judge:
1. `git checkout demo/main.py` (or manually revert the file to the error state).
2. Close unnecessary browser tabs.
3. Restart JARVIS to clear the in-memory task timeline.
