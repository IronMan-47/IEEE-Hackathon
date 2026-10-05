import { Proposal, ProposalStatus } from './types';
import { WorkspaceState, PatchOperationType } from '../workspace/types';
import { SafetyLimits, OperationRiskLevel } from '../safety/safety-limits';

export interface ValidationResult {
  valid: boolean;
  isStale: boolean;
  isExpired: boolean;
  riskLevel: OperationRiskLevel;
  isDestructive: boolean;
  errors: string[];
}

export class ProposalValidator {
  /**
   * Validates proposal schema, semantic operation integrity, revision freshness, expiration, and safety limits.
   */
  public static validate(proposal: Proposal, currentWorkspace: WorkspaceState): ValidationResult {
    const errors: string[] = [];
    let isStale = false;
    let isExpired = false;

    // 1. Schema Validation
    if (!proposal || typeof proposal !== 'object') {
      return {
        valid: false,
        isStale: false,
        isExpired: false,
        riskLevel: OperationRiskLevel.LOW,
        isDestructive: false,
        errors: ['Proposal object is null or invalid']
      };
    }

    if (!proposal.id || !proposal.title) {
      errors.push('Proposal missing required id or title');
    }

    if (!Array.isArray(proposal.operations) || proposal.operations.length === 0) {
      errors.push('Proposal must contain at least one patch operation');
    }

    // 2. Expiration Check (5 minutes limit)
    const now = Date.now();
    if (proposal.createdAt && (now - proposal.createdAt > SafetyLimits.PROPOSAL_EXPIRATION_MS)) {
      isExpired = true;
      errors.push(`EXPIRED PROPOSAL: Proposal generated at ${new Date(proposal.createdAt).toISOString()} exceeded expiration window of ${SafetyLimits.PROPOSAL_EXPIRATION_MS / 1000}s`);
    }

    // 3. Operation Count Safety Cap
    if (Array.isArray(proposal.operations) && proposal.operations.length > SafetyLimits.MAX_OPS_PER_PROPOSAL) {
      errors.push(`OPERATION LIMIT EXCEEDED: Proposal contains ${proposal.operations.length} ops (Max allowed: ${SafetyLimits.MAX_OPS_PER_PROPOSAL})`);
    }

    // 4. Optimistic Concurrency / Stale Revision Check
    if (typeof proposal.baseRevision !== 'number') {
      errors.push('Proposal missing baseRevision header');
    } else if (proposal.baseRevision !== currentWorkspace.revision) {
      isStale = true;
      errors.push(
        `STALE PROPOSAL: Built against workspace revision [ ${proposal.baseRevision} ], but current workspace revision is [ ${currentWorkspace.revision} ]`
      );
    }

    // 5. Semantic & Safety Limits Validation
    let isDestructive = false;
    let createCount = 0;

    if (Array.isArray(proposal.operations)) {
      for (let i = 0; i < proposal.operations.length; i++) {
        const op = proposal.operations[i];
        if (!op || !op.op || !op.targetId) {
          errors.push(`Operation index [ ${i} ] missing op type or targetId`);
          continue;
        }

        // Check if op type is known
        if (!Object.values(PatchOperationType).includes(op.op as PatchOperationType)) {
          errors.push(`Operation index [ ${i} ] has invalid op type: ${op.op}`);
        }

        // Target Element Existence Check
        if (op.op !== PatchOperationType.CREATE_ELEMENT) {
          const targetExists = Boolean(currentWorkspace.elements[op.targetId]);
          if (!targetExists) {
            errors.push(`Operation index [ ${i} ] targets non-existent element: [ ${op.targetId} ]`);
          }
        }

        // Protected Elements Check
        if (op.op === PatchOperationType.DELETE_ELEMENT) {
          isDestructive = true;
          if (SafetyLimits.isProtectedElement(op.targetId)) {
            errors.push(`PROTECTED ELEMENT VIOLATION: Cannot delete protected element [ ${op.targetId} ]`);
          }
        }

        if (op.op === PatchOperationType.CREATE_ELEMENT) {
          createCount++;
          if (createCount > SafetyLimits.MAX_ELEMENTS_CREATED) {
            errors.push(`SAFETY LIMIT VIOLATION: Exceeded max element creation cap (${SafetyLimits.MAX_ELEMENTS_CREATED})`);
          }
        }
      }
    }

    const riskLevel = SafetyLimits.classifyProposalRisk(proposal.operations || []);

    return {
      valid: errors.length === 0,
      isStale,
      isExpired,
      riskLevel,
      isDestructive,
      errors
    };
  }
}
