# Phase 5: Version Graph, Branching & Rollback

## Overview
Phase 5 introduces a real, local-first version-control system for **JARVIS — The Living Canvas**.
Workspace history is structured as a Directed Acyclic Graph (DAG) rather than a simple linear commit chain, supporting independent branch progression, historical checkout, canonical state hashing, domain diffing, and non-destructive rollbacks.

> **Core Invariant**: Every accepted and verified workspace mutation produces a new immutable version node. Rollbacks never delete history; instead, they commit a new version node capturing the restored historical state.

---

## Architectural Principles & Invariants

1. **Immutable History**: Once committed, a version node is frozen. State changes append new nodes.
2. **Deterministic Canonical Hashing**: SHA-256 computation of normalized workspace state (key-order independent).
3. **Branch Independence**: Branches diverge from any parent version and progress independently without mutating sibling branches.
4. **State Reconstruction**: Workspace state is reconstructed deterministically from root snapshots and operation lineages.
5. **Dirty State Safety Barrier**: Uncommitted manual edits (`DIRTY` state) block branch switching or version checkouts unless explicitly committed or discarded.
6. **Non-Destructive Rollback**: Rollbacks create a new commit node ($V_{rollback}$) linked to the current head, preserving full lineage history intact.
7. **Audit Logging Integration**: AuditLogger records structured events for all graph and branch state transitions.

---

## Version & Branch Schemas

### `WorkspaceVersion`
```typescript
export interface WorkspaceVersion {
  id: string;                      // Cryptographically or timestamped version ID
  workspaceId: string;             // Associated workspace identifier
  parentVersionId: string | null;  // Null for root V0 version
  branchId: string;                // Active branch ID
  revision: number;                // Monotonically increasing revision counter
  timestamp: number;               // Commit timestamp (ms)
  proposalId?: string;             // Associated proposal ID if AI-assisted
  author: 'HUMAN' | 'AI_ASSISTED'; // Author attribution
  type: 'MUTATION' | 'ROLLBACK' | 'INITIAL';
  sourceVersionId?: string;        // Set when type === 'ROLLBACK'
  operations: PatchOperation[];    // Operations applied in this version
  inverseOperations: InverseOperation[];
  stateHash: string;               // SHA-256 canonical state hash
  message: string;                 // Human-readable commit message
  snapshotState: WorkspaceState;   // Canonical workspace state snapshot
}
```

### `WorkspaceBranch`
```typescript
export interface WorkspaceBranch {
  id: string;
  workspaceId: string;
  name: string;
  headVersionId: string;
  createdFromVersionId: string;
  createdAt: number;
  status: 'ACTIVE' | 'ARCHIVED';
}
```

---

## Technical Features

### 1. Canonical State Hashing (`CanonicalHash`)
Normalizes element properties, style keys, and element IDs alphabetically before generating a SHA-256 digest:
$$\text{stateHash} = \text{SHA-256}(\text{CanonicalJSON}(\text{WorkspaceState}))$$

### 2. Domain Diff Engine (`DiffEngine`)
Computes domain-level differences between any two historical versions ($V_A$ and $V_B$):
- **Added Elements**: Elements present in $V_B$ but missing in $V_A$.
- **Removed Elements**: Elements present in $V_A$ but missing in $V_B$.
- **Modified Properties**: Changed values (e.g. width, height, label, style).
- **Moved Elements**: Spatial coordinates ($x, y$) changed.

### 3. Non-Destructive Rollback (`rollbackToVersion`)
Executing `rollbackToVersion(targetVersionId)`:
1. Reconstructs target state $S_{\text{target}}$ corresponding to `targetVersionId`.
2. Computes synthetic patch operations transforming current head state $S_{\text{current}} \rightarrow S_{\text{target}}$.
3. Commits a **new version node** ($V_{\text{rollback}}$) with `type: 'ROLLBACK'`, `sourceVersionId: targetVersionId`, and `parentVersionId: currentHeadId`.
4. Original history graph remains completely untouched.

### 4. Atomic Crash-Safe Local Persistence (`VersionStore`)
- Stores complete graph state in `.jarvis/workspace_history.json`.
- Uses atomic temporary file writes (`.tmp`) followed by atomic rename operations (`renameSync`).
- Verifies state hash integrity upon application restart.

---

## Verified Audit Events
- `VERSION_CREATED`
- `BRANCH_CREATED`
- `BRANCH_SWITCHED`
- `VERSION_CHECKED_OUT`
- `ROLLBACK_CREATED`
- `VERSION_DIFF_REQUESTED`
- `CONFLICT_DETECTED`
- `UNCOMMITTED_CHANGES_BLOCKED`
- `INTEGRITY_CHECK_FAILED`

---

## Test Verification
- **Automated Tests**: 54 total passing unit tests (45 TypeScript Vitest + 9 Python Pytest).
- **Manual Verification**: Electron Desktop App running on Windows with live Version Graph panel, branch switching select, branch creator modal, diff viewer, and rollback control.
