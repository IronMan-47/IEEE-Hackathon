# Phase 2 — Living Canvas Reference Adapter

## Executive Summary
Phase 2 builds the **Living Canvas** as a deterministic reference application adapter and testbed inside the JARVIS Windows Desktop Application.

The Living Canvas is **not** the final JARVIS product. Its purpose is to provide a safe, 100% controllable, unit-testable workspace environment to design and prove the core control loop:

$$\text{OBSERVE} \longrightarrow \text{UNDERSTAND} \longrightarrow \text{PLAN} \longrightarrow \text{PROPOSE} \longrightarrow \text{HUMAN APPROVAL} \longrightarrow \text{EXECUTE} \longrightarrow \text{VERIFY} \longrightarrow \text{COMMIT}$$

---

## 1. Domain Architecture (Isolated From UI & AI)

```
Living Canvas UI Layer (Renderer)
               │
               ▼
   Workspace Domain Model (Pure TS)
       ├── WorkspaceState (Revision, Elements)
       ├── Operations (Create, Update, Move, Delete, Resize, Style)
       └── Rollback Inverses
               │
               ▼
   Proposal Engine & Validator
       ├── Schema & Semantic Validation
       ├── Stale Revision Protection (Optimistic Concurrency)
       └── Human Control (Accept / Modify / Reject)
               │
               ▼
   Closed-Loop Verifier
       └── Actual Workspace Inspection vs Expected Property Check
```

---

## 2. Workspace Domain Model (`WorkspaceModel`)

### A. Element Schema
Every element maintains a stable unique identifier:
```json
{
  "id": "btn_pay",
  "type": "button",
  "x": 40,
  "y": 250,
  "w": 180,
  "h": 36,
  "label": "Pay Now (₹999)",
  "parentId": "card_main",
  "style": {
    "fill": "#475569",
    "color": "#CBD5E1",
    "borderRadius": 6,
    "fontSize": 13,
    "fontWeight": 400
  }
}
```

### B. Patch Operation Vocabulary
- `CREATE_ELEMENT`
- `UPDATE_ELEMENT`
- `DELETE_ELEMENT`
- `MOVE_ELEMENT`
- `RESIZE_ELEMENT`
- `UPDATE_STYLE`
- `UPDATE_TEXT`
- `GROUP_ELEMENTS`
- `UNGROUP_ELEMENTS`

---

## 3. Proposal Lifecycle & Stale Protection

### Proposal Schema
```typescript
interface Proposal {
  id: string;
  workspaceId: string;
  baseRevision: number;
  title: string;
  reason: string;
  operations: PatchOperation[];
  createdAt: number;
  source: 'AI' | 'HUMAN';
  status: ProposalStatus; // PENDING | APPROVED | REJECTED | MODIFIED | EXECUTED | VERIFIED | FAILED | STALE
}
```

### Stale Revision Protection (Optimistic Concurrency)
If the human edits the workspace while an AI proposal is pending:
1. Workspace revision increments ($1 \rightarrow 2$).
2. Pending proposal records `baseRevision: 1`.
3. Validator flags proposal as `STALE`.
4. Execution is **strictly blocked** to prevent overwriting user edits.

---

## 4. Human Approval & Control Loop

- **`[ Accept Proposal ]`:** Dispatches patch execution, computes inverse operations for rollback preparation, re-inspects actual domain state, and transitions status to `VERIFIED`.
- **`[ Modify Proposal ]`:** Allows the human to tweak parameters (e.g. adjust Pay button width from $320\text{px}$ to $280\text{px}$) prior to execution.
- **`[ Reject Proposal ]`:** Marks status as `REJECTED`. Workspace remains untouched ($Rev$ unchanged).

---

## 5. Automated Unit Test Matrix

| Test Suite | Tests | Result |
| :--- | :--- | :--- |
| `state-machine.test.ts` | Phase 1 State transitions & safety guards | **8/8 Passed** |
| `config.test.ts` | Phase 1 Configuration defaults & overrides | **2/2 Passed** |
| `logger.test.ts` | Phase 1 Structured logger output | **1/1 Passed** |
| `workspace-domain.test.ts` | Phase 2 Workspace operations, CRUD, stale detection, human decisions, closed-loop verification | **10/10 Passed** |
| **Total** | **4 Suites** | **21/21 Passed** |

---

## 6. Manual Windows Desktop Verification

| # | Verification Scenario | Status | Result |
|---|---|---|---|
| 1 | Living Canvas Split View | **PASSED** | 860x620 frameless overlay displays Checkout canvas on left, Proposal drawer on right. |
| 2 | Initial Checkout Scene | **PASSED** | Renders header, order summary, promo input, apply button, and Pay Now button. |
| 3 | AI Proposal Generation | **PASSED** | Generates *"Improve Checkout CTA Hierarchy"* proposal targeting `btn_pay` and `btn_coupon`. |
| 4 | Ghost Preview Layer | **PASSED** | Translucent cyan overlay outlines proposed target position/size on canvas. |
| 5 | Accept & Execute | **PASSED** | Enlarges Pay Now button ($180\text{px} \rightarrow 320\text{px}$), updates fill to cyan (`#06B6D4`), increments revision to $Rev 2$. |
| 6 | Closed-Loop Verification | **PASSED** | Re-inspects actual domain state post-execution; confirms `btn_pay.w === 320`; sets status to `VERIFIED`. |
| 7 | Reject Proposal | **PASSED** | Proposal transitions to `REJECTED`; workspace remains untouched at $Rev 1$. |
| 8 | Modify Proposal | **PASSED** | Human modifies button width to $280\text{px}$; executes successfully to $280\text{px}$. |
| 9 | Stale Proposal Guard | **PASSED** | Simulating manual edit bumps revision to $Rev 2$; pending proposal is flagged `STALE` and execution blocked. |
| 10 | Phase 1 Integrity | **PASSED** | System tray, `Ctrl+Shift+Space` overlay hotkey, and `Ctrl+Shift+F12` Emergency Stop operate flawlessly. |

---

## 7. Explicit Boundaries (Phase 2 Scope)
- ❌ **No LLM API calls** (Deterministic AI proposal engine used for testbed).
- ❌ **No Screen Capture / OCR / Computer Vision** (Scheduled for Phase 6).
- ❌ **No Mouse / Keyboard coordinate simulation** (Scheduled for Phase 9).
