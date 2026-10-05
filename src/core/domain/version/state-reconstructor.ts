import { WorkspaceState } from '../workspace/types';
import { WorkspaceVersion } from './types';
import { CanonicalHash } from './canonical-hash';

export class StateReconstructor {
  /**
   * Deterministically reconstructs the workspace state for a given version.
   * Validates reconstructed state against stateHash.
   */
  public static reconstructState(
    version: WorkspaceVersion,
    versionMap?: Map<string, WorkspaceVersion>
  ): WorkspaceState {
    if (!version) {
      throw new Error('StateReconstructor error: null version provided');
    }

    // Direct snapshot reconstruction
    const state: WorkspaceState = JSON.parse(JSON.stringify(version.snapshotState));

    // Verify hash integrity
    const hashMatches = CanonicalHash.verifyStateHash(state, version.stateHash);
    if (!hashMatches) {
      throw new Error(`StateReconstructor integrity failure: hash mismatch for version ${version.id}`);
    }

    return state;
  }

  /**
   * Reconstructs state by replaying operations from root (used as alternate verification path).
   */
  public static reconstructByReplay(
    targetVersionId: string,
    versionMap: Map<string, WorkspaceVersion>
  ): WorkspaceState {
    const lineage = StateReconstructor.getLineageFromRoot(targetVersionId, versionMap);
    if (lineage.length === 0) {
      throw new Error(`Target version [ ${targetVersionId} ] not found in version map`);
    }

    const rootVersion = lineage[0];
    let currentState: WorkspaceState = JSON.parse(JSON.stringify(rootVersion.snapshotState));

    for (let i = 1; i < lineage.length; i++) {
      const v = lineage[i];
      // Apply version operations to currentState
      currentState = StateReconstructor.applyOperationsToState(currentState, v.operations, v.revision);
    }

    return currentState;
  }

  public static getLineageFromRoot(
    versionId: string,
    versionMap: Map<string, WorkspaceVersion>
  ): WorkspaceVersion[] {
    const path: WorkspaceVersion[] = [];
    let curr: WorkspaceVersion | undefined = versionMap.get(versionId);

    while (curr) {
      path.unshift(curr);
      if (!curr.parentVersionId) break;
      curr = versionMap.get(curr.parentVersionId);
    }

    return path;
  }

  private static applyOperationsToState(
    state: WorkspaceState,
    ops: any[],
    targetRevision: number
  ): WorkspaceState {
    const newState: WorkspaceState = JSON.parse(JSON.stringify(state));
    newState.revision = targetRevision;
    newState.lastUpdated = Date.now();

    for (const op of ops) {
      switch (op.op) {
        case 'CREATE_ELEMENT':
          newState.elements[op.proposedValue.id] = JSON.parse(JSON.stringify(op.proposedValue));
          break;
        case 'DELETE_ELEMENT':
          delete newState.elements[op.targetId];
          break;
        case 'MOVE_ELEMENT':
          if (newState.elements[op.targetId]) {
            if (typeof op.proposedValue.x === 'number') newState.elements[op.targetId].x = op.proposedValue.x;
            if (typeof op.proposedValue.y === 'number') newState.elements[op.targetId].y = op.proposedValue.y;
          }
          break;
        case 'RESIZE_ELEMENT':
          if (newState.elements[op.targetId]) {
            if (typeof op.proposedValue.w === 'number') newState.elements[op.targetId].w = op.proposedValue.w;
            if (typeof op.proposedValue.h === 'number') newState.elements[op.targetId].h = op.proposedValue.h;
          }
          break;
        case 'UPDATE_STYLE':
          if (newState.elements[op.targetId]) {
            newState.elements[op.targetId].style = {
              ...newState.elements[op.targetId].style,
              ...op.proposedValue
            };
          }
          break;
        case 'UPDATE_TEXT':
          if (newState.elements[op.targetId]) {
            newState.elements[op.targetId].label = op.proposedValue.label;
          }
          break;
        case 'UPDATE_ELEMENT':
          if (newState.elements[op.targetId]) {
            const updates = op.proposedValue;
            if (typeof updates.x === 'number') newState.elements[op.targetId].x = updates.x;
            if (typeof updates.y === 'number') newState.elements[op.targetId].y = updates.y;
            if (typeof updates.w === 'number') newState.elements[op.targetId].w = updates.w;
            if (typeof updates.h === 'number') newState.elements[op.targetId].h = updates.h;
            if (typeof updates.label === 'string') newState.elements[op.targetId].label = updates.label;
            if (updates.style) {
              newState.elements[op.targetId].style = {
                ...newState.elements[op.targetId].style,
                ...updates.style
              };
            }
          }
          break;
      }
    }

    return newState;
  }
}
