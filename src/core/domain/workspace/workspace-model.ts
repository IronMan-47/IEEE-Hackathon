import {
  WorkspaceState,
  WorkspaceElement,
  PatchOperation,
  PatchOperationType,
  InverseOperation
} from './types';

export class WorkspaceModel {
  private state: WorkspaceState;

  constructor(initialState: WorkspaceState) {
    // Deep clone initial state
    this.state = JSON.parse(JSON.stringify(initialState));
  }

  public getState(): WorkspaceState {
    return JSON.parse(JSON.stringify(this.state));
  }

  public getRevision(): number {
    return this.state.revision;
  }

  public getElement(id: string): WorkspaceElement | undefined {
    return this.state.elements[id] ? JSON.parse(JSON.stringify(this.state.elements[id])) : undefined;
  }

  /**
   * Applies a batch of operations transactionally.
   * Increments workspace revision if all operations succeed.
   * Returns list of inverse operations for rollback preparation.
   */
  public applyPatch(ops: PatchOperation[]): { success: boolean; inverses: InverseOperation[]; error?: string } {
    const backup = JSON.parse(JSON.stringify(this.state)) as WorkspaceState;
    const inverses: InverseOperation[] = [];

    try {
      for (const op of ops) {
        const inverse = this.applySingleOperation(op);
        inverses.push(inverse);
      }

      // Success -> Increment revision
      this.state.revision += 1;
      this.state.lastUpdated = Date.now();

      return { success: true, inverses };
    } catch (err: unknown) {
      // Rollback memory state on error
      this.state = backup;
      return { success: false, inverses: [], error: String(err) };
    }
  }

  private applySingleOperation(op: PatchOperation): InverseOperation {
    const target = this.state.elements[op.targetId];

    switch (op.op) {
      case PatchOperationType.CREATE_ELEMENT: {
        const newEl = op.proposedValue as unknown as WorkspaceElement;
        if (!newEl || !newEl.id) {
          throw new Error(`CREATE_ELEMENT operation missing valid element data`);
        }
        if (this.state.elements[newEl.id]) {
          throw new Error(`Element [ ${newEl.id} ] already exists`);
        }
        this.state.elements[newEl.id] = JSON.parse(JSON.stringify(newEl));
        return {
          op: PatchOperationType.DELETE_ELEMENT,
          targetId: newEl.id,
          restoreValue: {}
        };
      }

      case PatchOperationType.DELETE_ELEMENT: {
        if (!target) {
          throw new Error(`Target element [ ${op.targetId} ] not found for DELETE_ELEMENT`);
        }
        const previousSnapshot = JSON.parse(JSON.stringify(target));
        delete this.state.elements[op.targetId];
        return {
          op: PatchOperationType.CREATE_ELEMENT,
          targetId: op.targetId,
          restoreValue: previousSnapshot
        };
      }

      case PatchOperationType.MOVE_ELEMENT: {
        if (!target) {
          throw new Error(`Target element [ ${op.targetId} ] not found for MOVE_ELEMENT`);
        }
        const prevX = target.x;
        const prevY = target.y;

        if (typeof op.proposedValue.x === 'number') target.x = op.proposedValue.x;
        if (typeof op.proposedValue.y === 'number') target.y = op.proposedValue.y;

        return {
          op: PatchOperationType.MOVE_ELEMENT,
          targetId: op.targetId,
          restoreValue: { x: prevX, y: prevY }
        };
      }

      case PatchOperationType.RESIZE_ELEMENT: {
        if (!target) {
          throw new Error(`Target element [ ${op.targetId} ] not found for RESIZE_ELEMENT`);
        }
        const prevW = target.w;
        const prevH = target.h;

        if (typeof op.proposedValue.w === 'number') target.w = op.proposedValue.w;
        if (typeof op.proposedValue.h === 'number') target.h = op.proposedValue.h;

        return {
          op: PatchOperationType.RESIZE_ELEMENT,
          targetId: op.targetId,
          restoreValue: { w: prevW, h: prevH }
        };
      }

      case PatchOperationType.UPDATE_STYLE: {
        if (!target) {
          throw new Error(`Target element [ ${op.targetId} ] not found for UPDATE_STYLE`);
        }
        const prevStyle = JSON.parse(JSON.stringify(target.style));
        target.style = {
          ...target.style,
          ...op.proposedValue
        };

        return {
          op: PatchOperationType.UPDATE_STYLE,
          targetId: op.targetId,
          restoreValue: prevStyle
        };
      }

      case PatchOperationType.UPDATE_TEXT: {
        if (!target) {
          throw new Error(`Target element [ ${op.targetId} ] not found for UPDATE_TEXT`);
        }
        const prevLabel = target.label || '';
        if (typeof op.proposedValue.label === 'string') {
          target.label = op.proposedValue.label;
        }

        return {
          op: PatchOperationType.UPDATE_TEXT,
          targetId: op.targetId,
          restoreValue: { label: prevLabel }
        };
      }

      case PatchOperationType.UPDATE_ELEMENT: {
        if (!target) {
          throw new Error(`Target element [ ${op.targetId} ] not found for UPDATE_ELEMENT`);
        }
        const previousSnapshot = JSON.parse(JSON.stringify(target));

        const updates = op.proposedValue as Partial<WorkspaceElement>;
        if (typeof updates.x === 'number') target.x = updates.x;
        if (typeof updates.y === 'number') target.y = updates.y;
        if (typeof updates.w === 'number') target.w = updates.w;
        if (typeof updates.h === 'number') target.h = updates.h;
        if (typeof updates.label === 'string') target.label = updates.label;
        if (updates.style) {
          target.style = { ...target.style, ...updates.style };
        }

        return {
          op: PatchOperationType.UPDATE_ELEMENT,
          targetId: op.targetId,
          restoreValue: previousSnapshot
        };
      }

      default:
        throw new Error(`Unsupported patch operation type: ${op.op}`);
    }
  }
}
