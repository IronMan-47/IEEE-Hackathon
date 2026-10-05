# Phase 1 — Real Windows Desktop Foundation

## Executive Summary
Phase 1 establishes the real, runnable Windows desktop foundation for **JARVIS**. 
The application runs as a native background desktop agent with system tray presence, a floating borderless dark overlay, OS-level global activation hotkeys, an authoritative state machine, and a hard emergency-stop safety mechanism.

---

## 1. Technology Decision Analysis

| Option | Technology | Evaluation for Windows Desktop AI Agent | Decision |
| :--- | :--- | :--- | :--- |
| **Option A (Chosen)** | **Electron (TypeScript / Node.js)** | • **Windows Overlay:** Excellent native support for frameless, transparent, `alwaysOnTop` desktop windows.<br>• **Global Hotkeys:** Built-in `globalShortcut` API captures `Ctrl+Shift+Space` globally across all active Windows apps.<br>• **System Tray:** Native Windows notification area tray integration with custom context menus.<br>• **Future Vision:** Native `desktopCapturer` APIs ready for Phase 6 screen perception. | **SELECTED** |
| Option B | **Tauri (Rust + Webview2)** | Low memory usage, but complex transparent overlay mouse pass-through on Windows Webview2 and requires Rust sidecar bridges for Python IPC. | Alternative Considered |
| Option C | **Python Native (PyQt/PySide)** | Single language, but modern borderless transparent overlays, smooth styling, and high-DPI scaling on Windows desktop are complex. | Alternative Considered |

---

## 2. Implemented Capabilities

### A. Authoritative State Machine
* **States:** `IDLE`, `READY`, `ACTIVE`, `STOPPED`, `ERROR`.
* **Transitions:**
  * `IDLE` $\rightarrow$ `READY` (on application initialization)
  * `READY` $\rightarrow$ `ACTIVE` (on global hotkey `Ctrl+Shift+Space` overlay open)
  * `ACTIVE` $\rightarrow$ `READY` (on overlay hide)
  * **ANY STATE** $\rightarrow$ `STOPPED` (on Emergency Stop shortcut `Ctrl+Shift+Escape` or tray menu click)
  * `STOPPED` $\rightarrow$ `READY` (on explicit user reset)
* **Safety Guard:** While in `STOPPED` state, activation shortcuts are **strictly blocked**.

### B. System Tray & Window Controls
* Native Windows System Tray icon displaying real-time JARVIS state.
* Context menu options: `Open JARVIS`, `Hide JARVIS`, `Global Activation Toggle`, `🛑 Emergency Stop`, `🔄 Reset to READY`, `Quit`.
* Closing the window hides it to the system tray instead of killing the background process.

### C. Typed IPC Contracts
All communications between Main Shell and Renderer UI pass through a secure context bridge (`preload.ts`) using strongly typed payloads (`StatusChangedPayload`, `JarvisConfigPayload`, `ErrorNotificationPayload`).

---

## 3. Automated Test Results
* Suite: `vitest` (3 test suites, 11 tests passed)
  * `state-machine.test.ts`: 8 tests verifying state transitions, emergency stop blocks, listener notifications.
  * `config.test.ts`: 2 tests verifying default hotkeys and option updates.
  * `logger.test.ts`: 1 test verifying structured log outputs.

---

## 4. Manual Windows Test Matrix

| # | Test Scenario | Action | Expected Result | Status |
|---|---|---|---|---|
| 1 | App Launch | Execute `npm start` | App launches, tray icon appears, state initializes to `READY`. | **PASSED** |
| 2 | Hide Window | Click Minimize or close window | Window hides to tray; background process remains active. | **PASSED** |
| 3 | Global Hotkey Show | Press `Ctrl+Shift+Space` in another app | JARVIS overlay appears on top; state transitions to `ACTIVE`. | **PASSED** |
| 4 | Global Hotkey Hide | Press `Ctrl+Shift+Space` again | Overlay hides; state transitions to `READY`. | **PASSED** |
| 5 | System Tray Menu | Click tray icon options | Toggle visibility, view state, enable/disable activation. | **PASSED** |
| 6 | Emergency Stop | Press `Ctrl+Shift+Escape` or tray click | State transitions to `STOPPED`; overlay hides; state indicator turns orange. | **PASSED** |
| 7 | Activation Guard | Press `Ctrl+Shift+Space` while `STOPPED` | Activation is suppressed; state remains `STOPPED`. | **PASSED** |
| 8 | Reactivation | Click "Reset to READY" in tray/UI | State machine resets to `READY`; hotkeys re-enabled. | **PASSED** |
| 9 | Clean Shutdown | Click "Quit JARVIS" in tray | Tray icon removed, global shortcuts unregistered, process terminates cleanly. | **PASSED** |

---

## 5. Explicit Limitations (Phase 1 Scope Boundary)
* **Screen Perception:** NOT implemented yet (Scheduled for Phase 6).
* **AI Model Reasoning:** NOT implemented yet (Scheduled for Phase 3).
* **Computer Interaction:** NOT implemented yet (Scheduled for Phase 9).
