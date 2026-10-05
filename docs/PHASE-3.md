# Phase 3 — Python Agent Core & AI Proposal Engine

## Executive Summary
Phase 3 introduces the **Python Agent Core** as the intelligence daemon behind JARVIS while preserving 100% of the Phase 1 and Phase 2 safety boundaries and execution contracts.

Natural language prompts flow through the Python Agent Core (Context Builder $\rightarrow$ Intent Classifier $\rightarrow$ Reasoning Planner $\rightarrow$ LLM Provider $\rightarrow$ Proposal Sanitizer) and produce structured JSON proposals. All validation, preview rendering, human decisions (`Accept`, `Modify`, `Reject`), patch execution, and post-execution verification remain strictly governed by the TypeScript Domain Engine.

---

## 1. System Architecture

```
                    JARVIS DESKTOP APPLICATION
                               │
             ┌─────────────────┴─────────────────┐
             │                                   │
       ELECTRON SHELL                     PYTHON AGENT CORE
    Overlay Window (860x620)               FastAPI Daemon
      System Tray / Hotkey             Listening on 127.0.0.1:8765
             │                                   │
             │           HTTP / IPC              │
             │  POST /agent/propose (JSON)       │
             └───────────────────────────────────┘
                                 │
                                 ▼
                     PYTHON AGENT PIPELINE
       Context Builder ──► Intent Classifier ──► Planner ──► Provider
                                 │
                                 ▼
                       Proposal Sanitizer
                                 │
                                 ▼
                         Structured Proposal
                                 │
                                 ▼
                      TYPESCRIPT DOMAIN ENGINE
       Schema Validator ──► Stale Guard ──► Preview Render
                                 │
                                 ▼
                           Human Approval
                     [ Accept / Modify / Reject ]
                                 │
                                 ▼
                            Patch Engine
                                 │
                                 ▼
                        Closed-Loop Verifier
```

---

## 2. Python Package Structure (`agent/`)

```
agent/
├── main.py                    # Entry point launching FastAPI via Uvicorn
├── core/
│   ├── agent.py               # Central JarvisAgent orchestrator
│   ├── config.py              # Environment configuration & provider selection
│   ├── logging.py             # Sanitized structured logger
│   └── types.py               # Data models (AgentRequest, AgentResponse, IntentCategory)
├── context/
│   └── workspace_context.py   # Workspace context parser
├── intent/
│   └── classifier.py          # Intent Classifier (PROPOSE_CHANGE, EXPLAIN_WORKSPACE, UNSUPPORTED)
├── reasoning/
│   ├── planner.py             # Reasoning planner producing candidate actions
│   ├── proposal_generator.py # Formats proposal schema via LLM provider
│   └── prompts.py             # System prompts & safety instructions
├── llm/
│   ├── provider.py            # Abstract LLMProvider interface
│   ├── gemini_provider.py     # Gemini GenAI SDK implementation
│   └── mock_provider.py       # Deterministic Mock Provider (Zero API Key fallback!)
├── proposals/
│   ├── schema.py              # Pydantic proposal & operation schemas
│   └── sanitizer.py           # Security sanitizer filtering illegal code/ops
└── transport/
    └── api.py                 # FastAPI endpoints (/health, /agent/propose)
```

---

## 3. Provider Abstraction & Config
* Mode selected via `JARVIS_LLM_PROVIDER`:
  * `mock` (default): Runs locally without an API key. Generates deterministic Checkout CTA hierarchy proposals.
  * `gemini`: Uses `google-genai` SDK with structured JSON output constraints (`response_mime_type="application/json"`).
* API keys (`GEMINI_API_KEY`) are read strictly from environment variables and are never logged or exposed to the renderer.

---

## 4. Security Sanitizer (`ProposalSanitizer`)
To ensure the LLM can never directly execute code or corrupt workspace state:
- Rejects unknown patch operations.
- Rejects operations targeting non-existent element IDs.
- Rejects raw JavaScript, Python, script tags (`<script>`), `eval()`, `exec()`, or shell commands.

---

## 5. Test Matrix (30 Total Passing Tests)

### A. Python Pytest Suite (9/9 Passed)
* `test_agent.py`: Request routing, intent classification, context parsing.
* `test_providers.py`: Mock provider output, simulated provider error handling.
* `test_sanitizer.py`: Valid schema check, op whitelist check, code injection rejection.

### B. TypeScript Vitest Suite (21/21 Passed)
* `state-machine.test.ts`: State transitions, emergency stop blocks (8 tests).
* `config.test.ts`: Configuration defaults (2 tests).
* `logger.test.ts`: Structured logger (1 test).
* `workspace-domain.test.ts`: Living Canvas CRUD, stale guards, human control, verification (10 tests).

---

## 6. Manual Windows Verification Results (Section 28)

| Scenario | Action | Result | Status |
| :--- | :--- | :--- | :--- |
| **Test 1: AI Proposal** | Prompt: *"Make Pay Now button more prominent"* | Python Agent receives context $\rightarrow$ Intent classified as `PROPOSE_CHANGE` $\rightarrow$ Mock LLM generates proposal $\rightarrow$ Sanitized $\rightarrow$ Overlay renders proposal preview. No auto-execution occurs. | **PASSED** |
| **Test 2: Human Approval** | Click `[ Accept Proposal ]` | Proposal passes `ProposalValidator` $\rightarrow$ Patch executed $\rightarrow$ Verifier confirms `btn_pay.w === 320` and `fill === '#06B6D4'` $\rightarrow$ Status `VERIFIED`. | **PASSED** |
| **Test 3: Rejection** | Click `[ Reject Proposal ]` | Proposal status becomes `REJECTED`; workspace remains untouched at $Rev 1$. | **PASSED** |
| **Test 4: Stale Proposal** | Generate proposal $\rightarrow$ Click "Simulate Stale Edit" | Workspace revision bumps to $Rev 2$; pending proposal is flagged `STALE` and execution blocked. | **PASSED** |
| **Test 5: LLM Failure** | Prompt: *"trigger_error"* | Python agent returns `status: "ERROR"`; Electron logs safe human-readable error *"Simulated LLM Provider Timeout"*; zero workspace mutation. | **PASSED** |
| **Test 6: Emergency Stop** | Press `Ctrl + Shift + F12` | System state becomes `STOPPED`; overlay hides; all proposal executions blocked. | **PASSED** |
