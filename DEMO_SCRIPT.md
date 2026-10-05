# JARVIS End-to-End Presentation Script

## Pre-Demo Setup
1. Open a terminal and start the JARVIS runtime: `npm start`
2. Open VS Code explicitly targeting the `demo/` folder. Open `main.py`.
3. Open a browser to a static mock documentation page (e.g., `mock_docs.html` or just a dummy search page).
4. Verify the JARVIS Living Overlay is visible in the bottom right corner of the screen.

## The Demonstration

### 1. Initiation
- **Presenter**: Show the VS Code editor with the deliberate `fake_legacy_module` import error.
- **Presenter**: Press `Ctrl+Shift+Space` to expand the JARVIS overlay.
- **Presenter**: Type (or use Voice): *"JARVIS, look at this error, find the relevant documentation in the browser, and propose a fix."*

### 2. Observation & Planning
- **JARVIS**: Transitions to `OBSERVING` state.
- **JARVIS**: UI updates to show `VS Code` as the active context.
- **JARVIS**: Transitions to `PLANNING`. The timeline reveals steps for cross-app research.

### 3. Cross-App Transition (VS Code → Browser)
- **Presenter**: Switch focus to the Browser window.
- **JARVIS**: Detects the handoff. Timeline displays `→ Handoff to browser`.
- **JARVIS**: Grounds the browser context, extracts evidence, and links it.

### 4. Cross-App Transition (Browser → VS Code)
- **Presenter**: Switch focus back to VS Code.
- **JARVIS**: Detects the return handoff. Timeline updates. Re-verifies file hash.

### 5. Proposal & Explanation
- **JARVIS**: Transitions to `WAITING_FOR_HUMAN`.
- **Presenter**: Click "Review Proposal" in the UI.
- **Presenter**: Show the structured proposal. Highlight the Risk Assessment and Explanation ("I found the new API documentation in the browser and propose updating the import").

### 6. Execution & Verification
- **Presenter**: Click "Approve & Execute".
- **JARVIS**: Token is minted. The file `main.py` is safely updated.
- **JARVIS**: Transitions to `VERIFYING`, then `COMPLETED`.
- **Presenter**: Show the corrected code in VS Code.

## Safety Demonstrations

### Failure Demo 1: Context Mismatch
- While JARVIS expects to switch to the Browser, deliberately switch to **Discord/Notepad**.
- **Expected**: JARVIS halts the workflow with `CROSS_APP_CONFLICT: Expected browser, found Discord`.

### Failure Demo 2: Staleness Block
- During the `WAITING_FOR_HUMAN` proposal stage, manually type a space into `main.py` and save.
- **Expected**: Upon clicking "Approve & Execute", the `ExecutionSafetyBarrier` blocks the action with `STALE PROPOSAL: Hash mismatch`.
