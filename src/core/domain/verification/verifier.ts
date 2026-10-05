import { Proposal } from '../proposal/types';
import { WorkspaceState, PatchOperationType } from '../workspace/types';

export interface VerificationResult {
  verified: boolean;
  timestamp: number;
  mismatchedProperties: string[];
}

export class Verifier {
  /**
   * Verifies actual workspace state against proposal's expected operations.
   * Does NOT assume execution succeeded merely because a function returned.
   */
  public static verifyProposalExecution(proposal: Proposal, actualState: WorkspaceState): VerificationResult {
    const mismatchedProperties: string[] = [];

    for (const op of proposal.operations) {
      const target = actualState.elements[op.targetId];

      switch (op.op) {
        case PatchOperationType.CREATE_ELEMENT:
          if (!target) {
            mismatchedProperties.push(`CREATE_ELEMENT: Target [ ${op.targetId} ] missing in actual workspace`);
          }
          break;

        case PatchOperationType.DELETE_ELEMENT:
          if (target) {
            mismatchedProperties.push(`DELETE_ELEMENT: Target [ ${op.targetId} ] still exists in actual workspace`);
          }
          break;

        case PatchOperationType.MOVE_ELEMENT:
          if (!target) {
            mismatchedProperties.push(`MOVE_ELEMENT: Target [ ${op.targetId} ] missing`);
          } else {
            if (typeof op.proposedValue.x === 'number' && target.x !== op.proposedValue.x) {
              mismatchedProperties.push(`MOVE_ELEMENT [ ${op.targetId} ]: x expected ${op.proposedValue.x}, got ${target.x}`);
            }
            if (typeof op.proposedValue.y === 'number' && target.y !== op.proposedValue.y) {
              mismatchedProperties.push(`MOVE_ELEMENT [ ${op.targetId} ]: y expected ${op.proposedValue.y}, got ${target.y}`);
            }
          }
          break;

        case PatchOperationType.RESIZE_ELEMENT:
          if (!target) {
            mismatchedProperties.push(`RESIZE_ELEMENT: Target [ ${op.targetId} ] missing`);
          } else {
            if (typeof op.proposedValue.w === 'number' && target.w !== op.proposedValue.w) {
              mismatchedProperties.push(`RESIZE_ELEMENT [ ${op.targetId} ]: w expected ${op.proposedValue.w}, got ${target.w}`);
            }
            if (typeof op.proposedValue.h === 'number' && target.h !== op.proposedValue.h) {
              mismatchedProperties.push(`RESIZE_ELEMENT [ ${op.targetId} ]: h expected ${op.proposedValue.h}, got ${target.h}`);
            }
          }
          break;

        case PatchOperationType.UPDATE_STYLE:
          if (!target) {
            mismatchedProperties.push(`UPDATE_STYLE: Target [ ${op.targetId} ] missing`);
          } else {
            for (const [key, val] of Object.entries(op.proposedValue)) {
              const actualVal = (target.style as Record<string, unknown>)[key];
              if (actualVal !== val) {
                mismatchedProperties.push(`UPDATE_STYLE [ ${op.targetId} ]: style.${key} expected ${String(val)}, got ${String(actualVal)}`);
              }
            }
          }
          break;

        case PatchOperationType.UPDATE_TEXT:
          if (!target) {
            mismatchedProperties.push(`UPDATE_TEXT: Target [ ${op.targetId} ] missing`);
          } else if (typeof op.proposedValue.label === 'string' && target.label !== op.proposedValue.label) {
            mismatchedProperties.push(`UPDATE_TEXT [ ${op.targetId} ]: label expected "${op.proposedValue.label}", got "${target.label}"`);
          }
          break;

        default:
          break;
      }
    }

    return {
      verified: mismatchedProperties.length === 0,
      timestamp: Date.now(),
      mismatchedProperties
    };
  }
}
