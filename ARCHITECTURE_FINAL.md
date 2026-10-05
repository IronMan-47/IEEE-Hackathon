# JARVIS Architecture

JARVIS implements a rigorous bounded execution model. The UI runs in a transparent Electron/React renderer, while the brain operates as a local Python process.

## Architecture Diagram

```mermaid
flowchart TD
    U([USER]) -->|TEXT / VOICE / HOTKEY| JO[JARVIS OVERLAY]
    JO -->|IPC| AR[AGENT RUNTIME]
    
    subgraph Python Backend
        AR --> PER[PERCEPTION]
        AR --> CF[CONTEXT FUSION]
        AR --> TE[TASK ENGINE]
        
        PER --> CF
        CF --> TE
        
        TE --> PL[PLANNER]
        PL --> PR[PROPOSAL]
    end
    
    PR -->|Pushed to UI| HA([HUMAN APPROVAL])
    HA -->|ApprovalToken| SB[SAFETY BARRIER]
    
    SB --> DR[DOMAIN ROUTER]
    
    DR --> LC[Living Canvas]
    DR --> VS[VS Code]
    DR --> BR[Browser]
    
    LC --> VF[VERIFICATION]
    VS --> VF
    BR --> VF
    
    VF --> VH[VERSION / HISTORY]
    VH --> U
```

## Subsystem Details
- **EventBus**: (`agent/runtime/event_bus.py`) All state transitions are idempotent and append-only.
- **Recovery**: (`agent/runtime/recovery.py`) A crash mid-execution resolves to `EXECUTION_UNCERTAIN`. JARVIS will NOT auto-retry without human re-grounding.
- **Audit**: (`agent/tasks/audit.py`) Extensive audit events (`AUDIT EVENT [PROPOSAL_CREATED]`) are emitted for tracing.
- **Provenance**: Phase 19 injected `WorkflowContextLink` objects that trace evidence extracted across applications.
- **Privacy Boundaries**: `ContextSanitizer` uses regex pattern matching over dictionary keys/values to redact potential passwords and API keys before they traverse execution environments.
