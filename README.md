# JARVIS — The Living Canvas
> **Human-Controlled Multimodal AI Computer Agent**

JARVIS is an intelligent AI layer that lives on the user's computer and understands what the user is currently doing directly inside their active workspace (VS Code, Chrome, Figma, AutoCAD, etc.).

---

## Authoritative Design Principle
> **"AI proposes. The human decides. The system verifies. The audit log records."**  
> Natural language prompts flow to the Python Agent Core to generate structured proposals. The LLM does NOT directly mutate workspace state. Every proposal must pass schema & stale validation, render a preview/diff, receive human sign-off (`[ Accept ]`, `[ Modify ]`, `[ Reject ]`), issue a single-use approval token, execute patch operations, and undergo closed-loop post-execution state verification.

---

## Phase 1, 2, 3, 4, 5, 6, 7 & 8 Capabilities Summary

- 🖥️ **Native Windows Desktop Shell:** Frameless translucent dark overlay ($860\times 620\text{px}$) with split workspace/proposal drawer layout.
- 📌 **System Tray Integration:** Real-time state indicator (`[ READY ]`, `[ ACTIVE ]`, `[ STOPPED ]`), activation toggles, and context menu.
- ⚡ **Global Shortcuts:** `Ctrl + Shift + Space` toggles overlay; `Ctrl + Shift + F12` triggers Emergency Stop.
- 🛑 **Emergency Stop Barrier:** Hard-blocks proposal execution, perception capture, and version graph mutations when system is in `STOPPED` state.
- 👁️ **Real Windows Desktop Perception:** Active application & window title detection via Win32 `ctypes` (`GetForegroundWindow`, `GetWindowTextW`, `GetWindowRect`, `GetWindowThreadProcessId`, `psutil`).
- 📸 **On-Demand Screenshot Capture:** Active window crop & full screen capture using `PIL.ImageGrab` with native GDI `BitBlt` fallback.
- 🏷️ **Application Classification Engine:** Categorizes processes into `CODE_EDITOR`, `BROWSER`, `DESIGN_TOOL`, `TERMINAL`, `DOCUMENT_EDITOR`, or `UNKNOWN`.
- 🔒 **Perception Policy & Privacy Boundaries:** Global perception toggle (`PERCEIVED_ENABLED` / `PERCEIVED_DISABLED`), excluded sensitive process blacklist (`1Password.exe`, `KeePass.exe`, `Bitwarden.exe`), and log privacy sanitization.
- 🔌 **Application Domain Adapters:** Specialized adapters (`LivingCanvasAdapter`, `VSCodeAdapter`, `BrowserAdapter`, `TerminalAdapter`, `FigmaAdapter`, `UnknownAdapter`) converting perception titles into structured application contexts.
- 🛡️ **Untrusted Data Boundary & Secret Redaction:** All application context strings are flagged with `_untrusted_data_boundary = True`; automatic parameter redaction (`?token=[REDACTED]`).
- 🧠 **Context-Aware Intent Understanding & Planning (Phase 8):** Request normalizer, hybrid intent classifier, target resolver, ambiguity detector (`ClarificationRequest`), goal & constraint extractor, non-executable plan step taxonomy (`OBSERVE`, `ANALYZE`, `REASON`, `PROPOSE`, `VERIFY`, `ASK_USER`), and safety validator.
- 📋 **Renderer Planning View UI:** Interactive strategy plan visualizer rendering Application Context, Classified Intent, Goals, Active Constraints, Plan Steps, Rationale, and Action Controls (`[ Edit Plan ]`, `[ Accept Plan ]`, `[ Reject ]`). NO execution primitives!
- 🌿 **Version Graph Engine (DAG):** Immutable version graph (`WorkspaceVersion`), multi-branch management (`WorkspaceBranch`), branch divergence, and root node initialization ($V_0$).
- 🔄 **State Reconstruction & SHA-256 Canonical Hashing:** Deterministic state reconstruction from operation lineages; property-order independent canonical SHA-256 state hashing (`CanonicalHash`).
- 🔍 **Domain Diff Engine:** Compares historical states and computes added, removed, modified, and moved elements (`DiffEngine`).
- ⏮️ **Non-Destructive Rollback:** Restores target historical workspace state by appending a *new* rollback version node ($V_{\text{rollback}}$); original history graph remains 100% intact.
- 💾 **Local-First Crash-Safe Persistence:** Atomic `.tmp` file write + rename strategy (`VersionStore`) surviving application restarts.
- 🔑 **Approval Token Authorization:** Single-use `ApprovalToken` binds human sign-off to exact proposal ID and revision; blocks duplicate executions.
- 📜 **Structured Audit Log:** Comprehensive audit trail recording request receipt, normalization, context selection, intent classification, goal extraction, constraint extraction, plan creation, plan validation, clarification, acceptance, and modification events.
- 🧪 **80 Passing Unit Tests:** 35 Pytest tests + 45 Vitest tests covering agent routing, intent classification, goal extraction, request normalization, plan validator, safety barriers, prompt injection defense, ambiguity detection, plan versioning, context relevance filtering, providers, sanitizer, state machine, config, logging, workspace domain, approval tokens, emergency stop barriers, version graph, branching, rollback, active window perception, and domain context adapters.

---

## Project Structure

```
JARVIS/
├── package.json              # App scripts and Electron dependencies
├── tsconfig.json             # TypeScript compiler settings
├── vitest.config.ts          # Vitest test suite configuration
├── pytest.ini                # Pytest configuration
│
├── agent/                    # PYTHON AGENT CORE DAEMON
│   ├── main.py               # Application launcher entry point
│   ├── core/                 # JarvisAgent orchestrator, config, logger, types
│   ├── context/              # ContextRelevanceFilter & RelevantContext
│   ├── adapters/             # BaseAdapter, AdapterRegistry, Sanitizer, App Adapters
│   ├── intent/               # RequestNormalizer, IntentClassifier, GoalExtractor, Models
│   ├── reasoning/            # Planner, PlanValidator, ProposalGenerator
│   ├── llm/                  # Provider Interface, MockProvider, GeminiProvider
│   └── transport/            # FastAPI routes (/health, /agent/perceive, /agent/plan)
│
├── src/                      # ELECTRON & TYPESCRIPT DOMAIN ENGINE
│   ├── core/
│   │   ├── state/            # State Machine & Types
│   │   ├── events/           # Typed IPC Channels & Messages
│   │   ├── config/           # Centralized Config Manager
│   │   ├── logging/          # Structured Logger
│   │   └── domain/           # WorkspaceModel, ProposalValidator, Verifier, ApprovalTokenManager, VersionGraph
│   └── apps/
│       └── desktop/
│           ├── main/         # WindowManager, TrayManager, ShortcutManager, IPCHandler, PythonProcessManager
│           └── renderer/     # Overlay UI, CanvasView, ProposalView, VersionView, PerceptionView, PlanningView
│
├── tests/
│   ├── python/               # Pytest suite (35 tests)
│   └── unit/                 # Vitest suite (45 tests)
│
└── README.md
```

---

## Quickstart Guide

```powershell
# 1. Install Node & Python dependencies
npm install
pip install fastapi uvicorn pydantic pytest requests google-genai

# 2. Compile TypeScript and copy static assets
npm run build

# 3. Run Unit Test Suites (80 total tests)
npm test                      # Vitest TypeScript tests (45 passed)
$env:PYTHONPATH="."; python -m pytest tests/python # Pytest Python tests (35 passed)

# 4. Launch Desktop Agent & Python Core Daemon
npm start
```


---

## ⚠️ Notes for the Next Antigravity Agent

Welcome! If you are picking up this project, here is a detailed breakdown of the exact state of the codebase, recent fixes, and hard-won architectural decisions you **MUST NOT REVERT**:

### 1. The Vanilla DOM Refactor (Do Not Use `innerHTML` for State Updates)
* **What Happened:** The previous architecture used a `syncState()` polling loop every 2 seconds that wiped `container.innerHTML` entirely. This physically destroyed the `<input>` DOM node while the user was typing, swallowing keystrokes and breaking Windows IME.
* **What I Did:** I completely rewrote `src/apps/desktop/renderer/components/overlay-view.ts`. It now uses an `initialRender()` function to mount the UI *once*, and an `updateDOM()` function that surgically mutates specific DOM elements (`document.getElementById(...)`).
* **Rule for You:** Do **not** revert to React-style `innerHTML` replacement for the command input or the root container. If you add new UI elements, update them granularly in `updateDOM()`. The `<input id="cmd-input">` node must remain permanently mounted.

### 2. Transparent Window Click-Through IPC
* **What Happened:** The transparent Electron `BrowserWindow` was instantiating at `860x620` to allow for future canvas expansion, but the invisible portions were swallowing clicks meant for the desktop beneath it.
* **What I Did:** I wired a `REQUEST_IGNORE_MOUSE_EVENTS` IPC bridge (`preload.ts`, `ipc-handler.ts`). In `overlay-view.ts`, I attached `mouseenter` and `mouseleave` listeners to the visible UI container. When the cursor leaves the JARVIS UI, Electron calls `win.setIgnoreMouseEvents(true, { forward: true })`, freeing the desktop underneath.
* **Rule for You:** Do not modify the window bounds to fix click-blocking. Rely on the IPC ignore-mouse toggles. 

### 3. "CURRENT APP" Dynamic Context Detection
* **What Happened:** The current app context was hardcoded to "Visual Studio Code" on the frontend.
* **What I Did:** I mapped `api.getApplicationContext()` to query the Python backend's `/agent/perceive` endpoint. The backend uses `user32.GetForegroundWindow()` via `active_window.py`. 
* **Rule for You:** In `app.ts`, there is an explicit filter that ignores active window names containing "jarvis" or "electron". This is because clicking the JARVIS input box makes JARVIS the foreground app, but we must preserve the *previous* application context (e.g., Chrome, VS Code) in the UI. **Do not remove this filter.**

### 4. Runtime Recovery & Release Packaging
* **What Happened:** `AgentRuntimeState` was crashing during snapshot recovery due to a Pydantic `active_step_id` mismatch, and PyInstaller bundled a broken executable entrypoint.
* **What I Did:** I fixed the persistence schemas in `runtime/lifecycle.py` and repointed the `run_agent.py` build script to explicitly trigger `agent.main.main`. 
* **Rule for You:** To generate a fresh release package, always run `npm run package` which natively compiles the TS, bundles the frontend, packages the Python backend via PyInstaller, and ships an NSIS Windows installer to `release/`.

Good luck! The UI is currently rendering beautifully and keyboard/mouse interaction is fully functional.
