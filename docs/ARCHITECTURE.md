# JARVIS Architecture Blueprint

## System Overview
JARVIS is a native Windows desktop AI agent. It operates directly over the user's active workspace (VS Code, Chrome, Figma, AutoCAD, etc.).

## Decoupled Multi-Process Architecture

```
                  ┌──────────────────────────────────────────────┐
                  │                 JARVIS SHELL                 │
                  │   Electron Overlay / System Tray / Hotkeys   │
                  └──────────────────────┬───────────────────────┘
                                         │ JSON-RPC / IPC Bridge
                  ┌──────────────────────▼───────────────────────┐
                  │              JARVIS AGENT CORE               │
                  │   Authoritative State Machine & IPC Handler  │
                  └──────────┬────────────────────────┬──────────┘
                             │                        │
        HTTP / Local Socket  │                        │ Local Function Calls
        POST /agent/plan     │                        │
                             ▼                        ▼
              ┌──────────────────────────┐  ┌──────────────────────────┐
              │    PYTHON AGENT CORE     │  │  TYPESCRIPT DOMAIN CORE  │
              │  (Relevance Filter /     │  │  (WorkspaceModel /       │
              │   Intent Classifier /    │  │   ProposalValidator /    │
              │   Goal Extractor /       │  │   Closed-Loop Verifier / │
              │   Planner & Validator)   │  │   Safety & Audit Layer)  │
              └──────────────────────────┘  └──────────────────────────┘
```

### 1. Desktop Shell Layer (Electron)
* Overlay window ($860\times 620\text{px}$), system tray integration, global activation (`Ctrl+Shift+Space`), and Emergency Stop (`Ctrl+Shift+F12`).
* Manages child process daemon lifecycle for Python Agent Core (`pythonProcessManager`).

### 2. Python Agent Core (`agent/`)
* **Transport:** FastAPI server on `http://127.0.0.1:8765`.
* **Orchestrator (`JarvisAgent`):** Normalizes user requests (`RequestNormalizer`), filters context (`ContextRelevanceFilter`), classifies intent (`IntentClassifier`), detects ambiguity (`ClarificationRequest`), extracts goals and constraints (`GoalExtractor`), formulates non-executable plans (`Planner`), and validates plan safety (`PlanValidator`).
* **Adapters (`agent/adapters/`):** Living Canvas, VS Code, Browser, Terminal, Figma, Unknown.
* **Security & Prompt Injection Defense:** All application context strings carry `_untrusted_data_boundary = True`. Zero execution primitives allowed in Phase 8 plans.

### 3. TypeScript Domain Engine (`src/core/domain/`)
* **Workspace Domain (`WorkspaceModel`):** Elements, revision tracking, CRUD operations, inverse patch generation.
* **Validator (`ProposalValidator`):** Schema validation, semantic element checks, expiration checks, protected element checks, and stale revision protection.
* **Approval Token Manager (`ApprovalTokenManager`):** Single-use execution authorization tokens binding approval to exact proposal ID and revision.
* **Safety Limits & Audit Logger:** Risk level classification (`LOW`, `MEDIUM`, `HIGH_DESTRUCTIVE`), protected elements, duplicate execution protection, structured audit logging (`AuditLogger`).
* **Closed-Loop Verifier (`Verifier`):** Inspects actual resulting workspace state post-execution; confirms target property matches.

---

## Technical Scope Matrix
* **Phase 1 (Complete):** Desktop Shell, System Tray, Global Hotkeys, Emergency Stop, State Machine, Config, Logging, Unit Tests.
* **Phase 2 (Complete):** Living Canvas Reference Adapter, Workspace Domain Model, Patch Vocabulary, Proposal Schema & Engine, Diff Inspector, Human Decision Controls, Stale Revision Detection, Closed-Loop Verification.
* **Phase 3 (Complete):** Python Agent Core Daemon, FastAPI Transport, Provider Abstraction (Mock & Gemini), Intent Classifier, Planner, Security Sanitizer, 30 Passing Tests.
* **Phase 4 (Complete):** Approval Tokens, Immutability & Modification History, Fresh Pre-execution Re-validation, Emergency Stop Hard Barrier, Operation Caps, Protected Elements, Destructive Confirmation, Audit Logging, 41 Passing Tests.
* **Phase 5 (Complete):** Version Graph Manager (DAG), Multi-Branch Management, Deterministic State Reconstruction, SHA-256 Canonical Hashing, Domain Diff Engine, Non-Destructive Rollback, Persistence Layer, Dirty-State Safety, 54 Passing Tests.
* **Phase 6 (Complete):** Real Windows Screen Perception, Active Window Detection (ctypes / psutil), GDI & ImageGrab Capture, Application Classifier, Perception Policy & Privacy Boundaries, 63 Passing Tests.
* **Phase 7 (Complete):** Application Context Adapters (Living Canvas, VS Code, Browser, Terminal, Figma, Unknown), Untrusted Data Boundary, Secret Parameter Redaction, 70 Passing Tests.
* **Phase 8 (Complete):** Context-Aware Intent Understanding & Planning, Hybrid Classifier, Goal/Constraint Extraction, Non-Executable Plan Step Taxonomy (`OBSERVE`, `ANALYZE`, `REASON`, `PROPOSE`, `VERIFY`, `ASK_USER`), Plan Safety Validator, Plan Versioning & Modification, Renderer Planning View UI, 80 Passing Tests (45 Vitest + 35 Pytest).
