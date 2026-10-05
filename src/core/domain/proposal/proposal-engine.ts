import { Proposal, ProposalStatus } from './types';
import { WorkspaceModel } from '../workspace/workspace-model';
import { PatchOperationType, PatchOperation } from '../workspace/types';
import { ProposalValidator, ValidationResult } from './validator';
import { Verifier, VerificationResult } from '../verification/verifier';
import { ApprovalTokenManager, ApprovalToken } from '../safety/approval-token';
import { AuditLogger, AuditEventType } from '../safety/audit-logger';
import { VersionGraphManager } from '../version/version-graph';

export class ProposalEngine {
  private activeProposal: Proposal | null = null;
  private isSystemReadyCallback: () => boolean;

  constructor(
    private workspaceModel: WorkspaceModel,
    isSystemReadyCallback?: () => boolean,
    private versionGraphManager?: VersionGraphManager
  ) {
    this.isSystemReadyCallback = isSystemReadyCallback || (() => true);
  }

  public getActiveProposal(): Proposal | null {
    return this.activeProposal ? JSON.parse(JSON.stringify(this.activeProposal)) : null;
  }

  /**
   * Deterministic Scenario Generator: Creates the "Improve Checkout CTA Hierarchy" proposal.
   */
  public generateCheckoutCtaProposal(): Proposal {
    const currentWorkspace = this.workspaceModel.getState();

    const operations: PatchOperation[] = [
      {
        op: PatchOperationType.UPDATE_ELEMENT,
        targetId: 'btn_pay',
        proposedValue: {
          x: 40,
          y: 250,
          w: 320,
          h: 46,
          label: 'Pay Now (₹999)',
          style: {
            fill: '#06B6D4',
            color: '#0F172A',
            fontSize: 15,
            fontWeight: 700
          }
        },
        reason: 'Enlarge primary CTA width (180px -> 320px) and apply high-contrast cyan fill to establish visual hierarchy.'
      },
      {
        op: PatchOperationType.UPDATE_ELEMENT,
        targetId: 'btn_coupon',
        proposedValue: {
          style: {
            fill: 'rgba(255, 255, 255, 0.08)',
            color: '#94A3B8',
            borderWidth: 1,
            borderColor: '#334155'
          }
        },
        reason: 'Subdue promo code button styling so it no longer competes with primary payment CTA.'
      }
    ];

    const proposal: Proposal = {
      id: `prop_${Date.now()}`,
      workspaceId: 'checkout_demo',
      baseRevision: currentWorkspace.revision,
      title: 'Improve Checkout CTA Hierarchy & Contrast',
      reason: 'The Pay Now CTA currently has weak visual weight (#475569) and smaller width than the form container, while the coupon button competes for attention.',
      operations,
      createdAt: Date.now(),
      source: 'AI',
      status: ProposalStatus.PENDING
    };

    const validation = ProposalValidator.validate(proposal, currentWorkspace);
    proposal.riskLevel = validation.riskLevel;
    proposal.isDestructive = validation.isDestructive;

    this.activeProposal = proposal;

    AuditLogger.logEvent(
      AuditEventType.PROPOSAL_CREATED,
      proposal.id,
      proposal.workspaceId,
      proposal.baseRevision,
      proposal.source,
      'SUCCESS',
      { title: proposal.title, riskLevel: proposal.riskLevel }
    );

    return this.getActiveProposal()!;
  }

  /**
   * Validates active proposal against current workspace state and safety limits.
   */
  public validateActiveProposal(): ValidationResult {
    if (!this.activeProposal) {
      return {
        valid: false,
        isStale: false,
        isExpired: false,
        riskLevel: 0 as any,
        isDestructive: false,
        errors: ['No active proposal to validate']
      };
    }

    const currentWorkspace = this.workspaceModel.getState();
    const result = ProposalValidator.validate(this.activeProposal, currentWorkspace);

    this.activeProposal.riskLevel = result.riskLevel;
    this.activeProposal.isDestructive = result.isDestructive;

    if (result.isExpired) {
      this.activeProposal.status = ProposalStatus.EXPIRED;
      this.activeProposal.statusReason = result.errors.join('; ');
      AuditLogger.logEvent(
        AuditEventType.PROPOSAL_STALE,
        this.activeProposal.id,
        this.activeProposal.workspaceId,
        currentWorkspace.revision,
        this.activeProposal.source,
        'EXPIRED',
        { errors: result.errors }
      );
    } else if (result.isStale) {
      this.activeProposal.status = ProposalStatus.STALE;
      this.activeProposal.statusReason = result.errors.join('; ');
      AuditLogger.logEvent(
        AuditEventType.PROPOSAL_STALE,
        this.activeProposal.id,
        this.activeProposal.workspaceId,
        currentWorkspace.revision,
        this.activeProposal.source,
        'STALE',
        { errors: result.errors }
      );
    } else if (!result.valid) {
      this.activeProposal.status = ProposalStatus.FAILED;
      this.activeProposal.statusReason = result.errors.join('; ');
      AuditLogger.logEvent(
        AuditEventType.PROPOSAL_VALIDATED,
        this.activeProposal.id,
        this.activeProposal.workspaceId,
        currentWorkspace.revision,
        this.activeProposal.source,
        'INVALID',
        { errors: result.errors }
      );
    }

    return result;
  }

  /**
   * Generates single-use execution Authorization Token for Human Approval.
   */
  public approveProposal(): { approved: boolean; token?: ApprovalToken; error?: string } {
    if (!this.activeProposal) {
      return { approved: false, error: 'No active proposal to approve' };
    }

    if (!this.isSystemReadyCallback()) {
      AuditLogger.logEvent(
        AuditEventType.EXECUTION_BLOCKED,
        this.activeProposal.id,
        this.activeProposal.workspaceId,
        this.activeProposal.baseRevision,
        'SAFETY_GATE',
        'BLOCKED',
        { reason: 'System in STOPPED state' }
      );
      return { approved: false, error: 'EXECUTION_BLOCKED: System is in STOPPED or ERROR state' };
    }

    const validation = this.validateActiveProposal();
    if (!validation.valid) {
      return { approved: false, error: `Validation failed: ${validation.errors.join('; ')}` };
    }

    const token = ApprovalTokenManager.generateToken(
      this.activeProposal.id,
      this.activeProposal.workspaceId,
      this.activeProposal.baseRevision
    );

    this.activeProposal.status = ProposalStatus.APPROVED;
    this.activeProposal.approvalToken = token.token;

    AuditLogger.logEvent(
      AuditEventType.PROPOSAL_APPROVED,
      this.activeProposal.id,
      this.activeProposal.workspaceId,
      this.activeProposal.baseRevision,
      'HUMAN',
      'APPROVED',
      { token: token.token }
    );

    return { approved: true, token };
  }

  /**
   * Human Control: Reject Proposal.
   */
  public rejectProposal(reason: string = 'User rejected proposal'): boolean {
    if (!this.activeProposal) return false;
    this.activeProposal.status = ProposalStatus.REJECTED;
    this.activeProposal.statusReason = reason;

    AuditLogger.logEvent(
      AuditEventType.PROPOSAL_REJECTED,
      this.activeProposal.id,
      this.activeProposal.workspaceId,
      this.activeProposal.baseRevision,
      'HUMAN',
      'REJECTED',
      { reason }
    );
    return true;
  }

  /**
   * Human Control: Modify Proposal parameters.
   * Immutability Preservation: Creates a new proposal ID linked to original proposal ID.
   */
  public modifyProposal(updatedOps: PatchOperation[]): boolean {
    if (!this.activeProposal) return false;
    if (this.activeProposal.status !== ProposalStatus.PENDING && this.activeProposal.status !== ProposalStatus.MODIFIED && this.activeProposal.status !== ProposalStatus.APPROVED) {
      return false;
    }

    const currentWorkspace = this.workspaceModel.getState();

    const modifiedProposal: Proposal = {
      id: `prop_mod_${Date.now()}`,
      workspaceId: this.activeProposal.workspaceId,
      baseRevision: currentWorkspace.revision,
      title: `[Modified] ${this.activeProposal.title}`,
      reason: `User modified proposal parameters from original [ ${this.activeProposal.id} ]`,
      operations: JSON.parse(JSON.stringify(updatedOps)),
      createdAt: Date.now(),
      source: 'HUMAN',
      status: ProposalStatus.MODIFIED,
      modifiedFromId: this.activeProposal.id
    };

    const validation = ProposalValidator.validate(modifiedProposal, currentWorkspace);
    modifiedProposal.riskLevel = validation.riskLevel;
    modifiedProposal.isDestructive = validation.isDestructive;

    this.activeProposal = modifiedProposal;

    AuditLogger.logEvent(
      AuditEventType.PROPOSAL_MODIFIED,
      modifiedProposal.id,
      modifiedProposal.workspaceId,
      modifiedProposal.baseRevision,
      'HUMAN',
      'MODIFIED',
      { modifiedFromId: modifiedProposal.modifiedFromId, valid: validation.valid }
    );

    return validation.valid;
  }

  /**
   * Human Control: Execute Proposal with Single-Use Authorization Token.
   * Enforces:
   * 1. Emergency Stop Barrier
   * 2. Single-Use Approval Token Verification
   * 3. Duplicate Execution Protection
   * 4. Fresh Re-Validation Immediately Before Execution
   * 5. Post-Execution Verification
   */
  public acceptAndExecuteProposal(approvalTokenString?: string): { success: boolean; verification?: VerificationResult; error?: string } {
    if (!this.activeProposal) {
      return { success: false, error: 'No active proposal to execute' };
    }

    // 1. Hard Execution Barrier: Emergency Stop Block
    if (!this.isSystemReadyCallback()) {
      AuditLogger.logEvent(
        AuditEventType.EXECUTION_BLOCKED,
        this.activeProposal.id,
        this.activeProposal.workspaceId,
        this.activeProposal.baseRevision,
        'SAFETY_BARRIER',
        'BLOCKED',
        { reason: 'System in STOPPED state' }
      );
      return { success: false, error: 'EXECUTION_BLOCKED: System is in STOPPED state' };
    }

    // 2. Duplicate Execution Protection
    if (
      this.activeProposal.status === ProposalStatus.REJECTED ||
      this.activeProposal.status === ProposalStatus.STALE ||
      this.activeProposal.status === ProposalStatus.VERIFIED ||
      this.activeProposal.status === ProposalStatus.EXECUTED ||
      this.activeProposal.status === ProposalStatus.EXPIRED
    ) {
      AuditLogger.logEvent(
        AuditEventType.EXECUTION_BLOCKED,
        this.activeProposal.id,
        this.activeProposal.workspaceId,
        this.activeProposal.baseRevision,
        'DUPLICATE_GUARD',
        'BLOCKED',
        { status: this.activeProposal.status }
      );
      return {
        success: false,
        error: `DUPLICATE_EXECUTION_BLOCKED: Proposal in status [ ${this.activeProposal.status} ] cannot be executed`
      };
    }

    // 3. Approval Token Authorization Verification
    const tokenToVerify = approvalTokenString || this.activeProposal.approvalToken;
    if (!tokenToVerify) {
      return { success: false, error: 'EXECUTION_UNAUTHORIZED: Missing single-use approval authorization token' };
    }

    const tokenVerification = ApprovalTokenManager.verifyAndConsumeToken(
      tokenToVerify,
      this.activeProposal.id,
      this.activeProposal.workspaceId,
      this.activeProposal.baseRevision
    );

    if (!tokenVerification.valid) {
      AuditLogger.logEvent(
        AuditEventType.EXECUTION_BLOCKED,
        this.activeProposal.id,
        this.activeProposal.workspaceId,
        this.activeProposal.baseRevision,
        'TOKEN_VERIFIER',
        'UNAUTHORIZED',
        { error: tokenVerification.error }
      );
      return { success: false, error: tokenVerification.error };
    }

    // 4. Fresh Re-Validation Immediately Before Execution
    const freshValidation = this.validateActiveProposal();
    if (!freshValidation.valid) {
      AuditLogger.logEvent(
        AuditEventType.EXECUTION_BLOCKED,
        this.activeProposal.id,
        this.activeProposal.workspaceId,
        this.activeProposal.baseRevision,
        'RE_VALIDATOR',
        'INVALID',
        { errors: freshValidation.errors }
      );
      return { success: false, error: `Fresh Pre-execution Validation Failed: ${freshValidation.errors.join('; ')}` };
    }

    AuditLogger.logEvent(
      AuditEventType.EXECUTION_STARTED,
      this.activeProposal.id,
      this.activeProposal.workspaceId,
      this.activeProposal.baseRevision,
      'ENGINE',
      'START'
    );

    // 5. Execute Patch on Workspace Domain Model
    const patchResult = this.workspaceModel.applyPatch(this.activeProposal.operations);
    if (!patchResult.success) {
      this.activeProposal.status = ProposalStatus.FAILED;
      this.activeProposal.statusReason = patchResult.error;
      AuditLogger.logEvent(
        AuditEventType.EXECUTION_COMPLETED,
        this.activeProposal.id,
        this.activeProposal.workspaceId,
        this.activeProposal.baseRevision,
        'PATCH_ENGINE',
        'FAILED',
        { error: patchResult.error }
      );
      return { success: false, error: patchResult.error };
    }

    this.activeProposal.status = ProposalStatus.EXECUTED;

    // 6. Closed-Loop Post-Execution Verification
    const actualWorkspace = this.workspaceModel.getState();
    const verification = Verifier.verifyProposalExecution(this.activeProposal, actualWorkspace);

    if (verification.verified) {
      this.activeProposal.status = ProposalStatus.VERIFIED;
      AuditLogger.logEvent(
        AuditEventType.VERIFICATION_PASSED,
        this.activeProposal.id,
        this.activeProposal.workspaceId,
        actualWorkspace.revision,
        'VERIFIER',
        'VERIFIED'
      );

      if (this.versionGraphManager) {
        this.versionGraphManager.commitVersion({
          workspaceId: this.activeProposal.workspaceId,
          operations: this.activeProposal.operations,
          inverseOperations: patchResult.inverses,
          state: actualWorkspace,
          author: this.activeProposal.source === 'HUMAN' ? 'HUMAN' : 'AI_ASSISTED',
          proposalId: this.activeProposal.id,
          message: this.activeProposal.title,
          type: 'MUTATION'
        });
      }
    } else {
      this.activeProposal.status = ProposalStatus.FAILED;
      this.activeProposal.statusReason = `Verification failed: ${verification.mismatchedProperties.join('; ')}`;
      AuditLogger.logEvent(
        AuditEventType.VERIFICATION_FAILED,
        this.activeProposal.id,
        this.activeProposal.workspaceId,
        actualWorkspace.revision,
        'VERIFIER',
        'FAILED',
        { mismatches: verification.mismatchedProperties }
      );
    }

    return {
      success: verification.verified,
      verification
    };
  }
}
