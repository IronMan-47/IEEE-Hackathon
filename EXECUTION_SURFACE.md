# JARVIS Execution Surface Audit

JARVIS adheres to a strict **"AI Proposes. Human Decides."** safety boundary. It possesses absolutely zero generic OS automation (no `pyautogui`, no uncontrolled terminal/PowerShell access). 

Every execution primitive is strictly bounded, typed, explicitly validated by the `DomainRouter` and `ExecutionSafetyBarrier`, requires a single-use cryptographically hashed `ApprovalToken`, and executes via a deterministic `DomainExecutor`.

## 1. Visual Studio Code (VS Code) Executor
**Domain**: `vscode`
**Executor**: `agent/execution/vscode_executor.py`
**Validation**: Verifies target file exists in the active workspace and the Base Context Hash matches the current file hash (Staleness Protection).

| Operation | Input Schema | Risk Level | Approval Required | Verification | Rollback Behavior |
|-----------|--------------|------------|-------------------|--------------|-------------------|
| `UPDATE_FILE` | `{ "content": "..." }` | HIGH | YES | Verifies modified AST parses successfully | Reverts document content on verification failure |
| `FORMAT_CODE` | `{ "target": "file.ts" }` | LOW | YES | Verifies file hash changed | User can undo in VS Code |
| `REFACTOR_CODE` | `{ "range": "10-20", "content": "..." }` | HIGH | YES | Verifies AST parses successfully | Reverts document content on verification failure |

## 2. Browser Executor
**Domain**: `browser`
**Executor**: `agent/execution/browser_executor.py`
**Validation**: Explicit URL matching, cross-origin blocks (Staleness Protection via Origin hashing), and keyword-based risk assessment.

| Operation | Input Schema | Risk Level | Approval Required | Verification | Rollback Behavior |
|-----------|--------------|------------|-------------------|--------------|-------------------|
| `NAVIGATE` | `{ "url": "https://..." }` | MEDIUM | YES | Verifies window location matches URL | Browser back action |
| `CLICK` | `{ "selector": "#btn" }` | VARIES* | YES | Confirms element exists and is clickable | Irreversible (State machine relies on human validation) |
| `INPUT` | `{ "selector": "#q", "value": "..." }` | LOW | YES | Confirms DOM element value changed | Irreversible |

*\* Clicking high-risk targets (e.g., `#delete_account`, `#pay`) forces `HIGH` risk classification and mandates strict secondary authorization.*

## 3. Living Canvas (Reference Environment)
**Domain**: `living_canvas`
**Executor**: `agent/core/agent.py` (Canvas API)
**Validation**: Verifies workspace revision against Proposal base revision.

| Operation | Input Schema | Risk Level | Approval Required | Verification | Rollback Behavior |
|-----------|--------------|------------|-------------------|--------------|-------------------|
| `UPDATE_STYLE` | `{ "elementId": "header", "css": "..." }` | LOW | YES | Confirms AST property diff | Version Graph standard rollback |
| `UPDATE_CANVAS`| `{ "delta": {...} }` | LOW | YES | Confirms revision bumped | Version Graph standard rollback |

## Intentional Limitations
1. **No Application Launching**: JARVIS cannot launch an application. It relies entirely on the human to open applications and present them to JARVIS via the Windows OS active window API.
2. **No Arbitrary Shell**: JARVIS cannot run `bash`, `cmd`, or `powershell` commands.
3. **No Unrestricted Filesystem Access**: Execution in VS Code is sandboxed to the active workspace.
4. **No UI Automation via Coordinates**: `CLICK` relies strictly on semantic DOM selectors, preventing chaotic click automation if window sizes change.
