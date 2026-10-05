import { PatchOperation, PatchOperationType } from '../workspace/types';

export enum OperationRiskLevel {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH_DESTRUCTIVE = 'HIGH (DESTRUCTIVE)'
}

export class SafetyLimits {
  public static readonly MAX_OPS_PER_PROPOSAL = 10;
  public static readonly MAX_ELEMENTS_CREATED = 5;
  public static readonly MAX_MOVE_DELTA_PX = 800;
  public static readonly MAX_RESIZE_DELTA_PX = 800;
  public static readonly PROPOSAL_EXPIRATION_MS = 300000; // 5 minutes

  public static readonly PROTECTED_ELEMENT_IDS = ['card_main', 'workspace-root', 'system_header'];

  /**
   * Classifies the overall risk level of a proposal based on its operation types.
   */
  public static classifyProposalRisk(operations: PatchOperation[]): OperationRiskLevel {
    let hasDestructive = false;
    let hasStructural = false;

    for (const op of operations) {
      if (op.op === PatchOperationType.DELETE_ELEMENT) {
        hasDestructive = true;
      }
      if (op.op === PatchOperationType.CREATE_ELEMENT || op.op === PatchOperationType.GROUP_ELEMENTS || op.op === PatchOperationType.UNGROUP_ELEMENTS) {
        hasStructural = true;
      }
    }

    if (hasDestructive) return OperationRiskLevel.HIGH_DESTRUCTIVE;
    if (hasStructural) return OperationRiskLevel.MEDIUM;
    return OperationRiskLevel.LOW;
  }

  /**
   * Checks if an operation touches a protected element.
   */
  public static isProtectedElement(elementId: string): boolean {
    return SafetyLimits.PROTECTED_ELEMENT_IDS.includes(elementId);
  }
}
