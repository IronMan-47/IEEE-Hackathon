# FINAL EVALUATION FIX LIST

This document outlines the exact sequence of repairs required to address the critical and important defects discovered during the independent evaluation.

## PRIORITY 0: EMERGENCY STOP BACKEND PIPELINE
**Type:** IMPORTANT DEFECT
**Component:** Frontend IPC & Backend API

1. **Python API Update (`agent/transport/api.py`)**
   * Create a `@app.post("/api/runtime/stop")` endpoint.
   * Inside the endpoint, call `runtime_manager.trigger_emergency_stop()`.
   * Ensure it returns a `{ "status": "STOPPED" }` payload.

2. **Frontend IPC Update (`src/apps/desktop/main/ipc-handler.ts`)**
   * In `ipcMain.handle(IPCChannel.REQUEST_EMERGENCY_STOP)`, after transitioning the TS state machine, issue an HTTP POST request to `http://localhost:<PORT>/api/runtime/stop`.
   * Guarantee that the global hotkey `Ctrl+Shift+Escape` successfully triggers this IPC channel and halts Python backend loops.

## PRIORITY 1: AI PIPELINE INTEGRATION
**Type:** CRITICAL BLOCKER
**Component:** Backend Reasoning & Proposals

1. **Prompt & Schema Alignment (`agent/llm/gemini_provider.py`)**
   * Update the `generate_proposal` prompt to expect the modern Phase 15 multi-domain JSON schema (utilizing `op_type`, `target`, and `parameters`), explicitly replacing the legacy `PatchOperationSchema`.
   * Ensure the output adheres strictly to the canonical operations mapped in `agent/core/operations.py`.

2. **Orchestrator De-Mocking (`agent/proposals/generator.py`)**
   * Remove all hardcoded demo sequences (`btn_pay`, `example.com`, etc.) from `_build_operations_for_domain`.
   * Refactor `generate_from_plan` to inject and await `agent.reasoning.proposal_generator.Phase3ProposalGenerator`.
   * Serialize the LLM JSON response explicitly into `Proposal` and `ProposalOperation` Pydantic domain models.

3. **Planner LLM Integration (`agent/reasoning/planner.py`)**
   * Remove the hardcoded `PlanStep` generation based on `IntentCategory`.
   * Wire the `Planner` to invoke a dedicated LLM prompt that dynamically generates `PlanStep` lists based on the grounded `WorkspaceContextModel` and actual user request.

## PRIORITY 2: UX DE-MOCKING
**Type:** POLISH / IMPROVEMENT
**Component:** Frontend Orchestration

1. **Voice Transcript Simulation (`src/apps/desktop/main/ipc-handler.ts`)**
   * Re-verify that `processVoiceSpeech` gracefully communicates with `/agent/voice/process`. Maintain the documented SIMULATED state unless a true STT streaming module is implemented.

2. **Terminal / Figma UX Warnings (`agent/execution/domain_router.py`)**
   * Ensure any attempt to route to `Terminal` or `Figma` explicitly returns an `UNAVAILABLE` block state to the frontend, preventing silent drops or false success. 
