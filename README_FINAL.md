# JARVIS - Living Canvas

**JARVIS** is a human-controlled Windows desktop AI agent that understands context across applications, proposes structured actions, executes only approved bounded operations, and verifies the result.

JARVIS embraces the core philosophy: **"AI Proposes. Human Decides. Context may flow. Authority cannot."**

## What Problem Does It Solve?
AI agents often operate as either powerless chatbots or dangerous, unrestricted autonomous actors (`os.system(...)`, generic `pyautogui` clicking). JARVIS bridges this gap by acting as a native OS-level "Living Overlay." It grounds its context in what the user is actively seeing (VS Code, Browser, Living Canvas), proposes strongly-typed and reversible operations, and waits for explicit human cryptographic approval before executing.

## How the Architecture Works
JARVIS is split between a **Python Agent Runtime** and an **Electron/React UI Shell**.
1. **Perception**: Uses OS-level active window inspection and multimodal vision to parse the user's screen.
2. **Context Fusion**: Merges OCR, accessibility trees, and source code into a hashed `GroundedContext`.
3. **Task Orchestration**: Plans multi-step workflows.
4. **Handoffs**: Can extract sanitized evidence from one app (Browser) and transition it to another (VS Code).
5. **Execution Safety**: Relies on a strict `DomainExecutor` pattern backed by an `ApprovalToken` minting process.

## What It Can Do
- Ground itself in VS Code, Browser, and Living Canvas.
- Understand errors in active windows.
- Perform multi-step cross-application research workflows.
- Propose `UPDATE_FILE`, `FORMAT_CODE`, `NAVIGATE`, `CLICK` and more.
- Rollback its own changes via a native Version Graph.
- Stop immediately via a global Emergency Stop.

## What It Cannot Do (Intentionally)
- Run arbitrary Python code or shell scripts.
- Use generic `pyautogui` or coordinate-based mouse automation.
- Launch applications automatically.
- Steal execution authority without explicit UI approval.
- Exfiltrate secrets across cross-application handoff boundaries.

## Running JARVIS
### Prerequisites
- Windows OS
- Node 18+
- Python 3.10+
- `npm install`
- `pip install -r requirements.txt` (or appropriate python environment)

### Start
Start the Python Agent daemon and the Electron app:
```bash
npm start
```
*Note: Ensure the local Python Agent is running. See `agent/core/main.py` if testing headless.*
