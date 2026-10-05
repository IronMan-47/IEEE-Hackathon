import { describe, it, expect, beforeEach, vi } from 'vitest';
import { WorkspaceModel } from '../../core/domain/workspace/workspace-model';
import { createCheckoutInitialScene } from '../../core/domain/workspace/checkout-scene';
import { ProposalEngine } from '../../core/domain/proposal/proposal-engine';
import { ProposalStatus } from '../../core/domain/proposal/types';
import { PatchOperationType, PatchOperation } from '../../core/domain/workspace/types';
import { ApprovalTokenManager } from '../../core/domain/safety/approval-token';
import { AuditLogger, AuditEventType } from '../../core/domain/safety/audit-logger';
import { SafetyLimits, OperationRiskLevel } from '../../core/domain/safety/safety-limits';

describe('Phase 4 — Safety Hardening & Human Control Unit Tests', () => {
  let model: WorkspaceModel;
  let engine: ProposalEngine;
  let isReadyState = true;

  beforeEach(() => {
    isReadyState = true;
    model = new WorkspaceModel(createCheckoutInitialScene());
    engine = new ProposalEngine(model, () => isReadyState);
    AuditLogger.clear();
  });

  // --- APPROVAL TOKEN & DUPLICATE EXECUTION TESTS ---
  describe('Approval Token & Execution Authorization', () => {
    it('generates a single-use approval token upon approval', () => {
      engine.generateCheckoutCtaProposal();
      const approveRes = engine.approveProposal();

      expect(approveRes.approved).toBe(true);
      expect(approveRes.token).toBeDefined();
      expect(approveRes.token?.token).toContain('auth_tok_');
    });

    it('REJECTS execution when approval token is missing or invalid', () => {
      engine.generateCheckoutCtaProposal();
      engine.approveProposal();

      const execRes = engine.acceptAndExecuteProposal('invalid_token_xyz');
      expect(execRes.success).toBe(false);
      expect(execRes.error).toContain('token not found or invalid');
    });

    it('PREVENTS duplicate execution using the same token twice', () => {
      engine.generateCheckoutCtaProposal();
      const approveRes = engine.approveProposal();
      const tokenString = approveRes.token!.token;

      // First execution -> Success
      const firstExec = engine.acceptAndExecuteProposal(tokenString);
      expect(firstExec.success).toBe(true);

      // Second execution -> Rejection!
      const secondExec = engine.acceptAndExecuteProposal(tokenString);
      expect(secondExec.success).toBe(false);
      expect(secondExec.error).toContain('DUPLICATE_EXECUTION_BLOCKED');
    });
  });

  // --- EMERGENCY STOP HARD EXECUTION BARRIER ---
  describe('Emergency Stop Execution Barrier', () => {
    it('HARD-BLOCKS proposal execution when system is in STOPPED state', () => {
      engine.generateCheckoutCtaProposal();
      const approveRes = engine.approveProposal();

      // Trigger Emergency Stop (System not ready)
      isReadyState = false;

      const execRes = engine.acceptAndExecuteProposal(approveRes.token!.token);
      expect(execRes.success).toBe(false);
      expect(execRes.error).toContain('EXECUTION_BLOCKED: System is in STOPPED state');

      // Verify workspace remained untouched
      expect(model.getRevision()).toBe(1);
    });

    it('HARD-BLOCKS approval token generation when system is in STOPPED state', () => {
      engine.generateCheckoutCtaProposal();
      isReadyState = false;

      const approveRes = engine.approveProposal();
      expect(approveRes.approved).toBe(false);
      expect(approveRes.error).toContain('STOPPED');
    });
  });

  // --- PROPOSAL IMMUTABILITY & MODIFICATION HISTORY ---
  describe('Proposal Immutability & Re-Validation', () => {
    it('creates a new proposal object linked to original ID when modified', () => {
      const originalProp = engine.generateCheckoutCtaProposal();
      const originalId = originalProp.id;

      const updatedOps: PatchOperation[] = [
        {
          op: PatchOperationType.UPDATE_ELEMENT,
          targetId: 'btn_pay',
          proposedValue: { w: 290 },
          reason: 'Human modified width to 290px'
        }
      ];

      const modOk = engine.modifyProposal(updatedOps);
      expect(modOk).toBe(true);

      const modifiedProp = engine.getActiveProposal()!;
      expect(modifiedProp.id).not.toBe(originalId);
      expect(modifiedProp.modifiedFromId).toBe(originalId);
      expect(modifiedProp.source).toBe('HUMAN');
      expect(modifiedProp.status).toBe(ProposalStatus.MODIFIED);
    });

    it('re-validates modified proposal against safety limits', () => {
      engine.generateCheckoutCtaProposal();

      // Attempt to modify with an invalid operation targeting protected element deletion
      const invalidOps: PatchOperation[] = [
        {
          op: PatchOperationType.DELETE_ELEMENT,
          targetId: 'card_main', // Protected element!
          proposedValue: {},
          reason: 'Illegal delete protected element'
        }
      ];

      const modOk = engine.modifyProposal(invalidOps);
      expect(modOk).toBe(false); // Must be rejected by validator
    });
  });

  // --- SAFETY LIMITS & PROTECTED ELEMENTS ---
  describe('Safety Limits & Protected Elements', () => {
    it('classifies proposals containing DELETE_ELEMENT as HIGH (DESTRUCTIVE) risk', () => {
      const ops: PatchOperation[] = [
        {
          op: PatchOperationType.DELETE_ELEMENT,
          targetId: 'btn_coupon',
          proposedValue: {},
          reason: 'Delete coupon button'
        }
      ];

      const risk = SafetyLimits.classifyProposalRisk(ops);
      expect(risk).toBe(OperationRiskLevel.HIGH_DESTRUCTIVE);
    });

    it('blocks deletion of protected structural elements (card_main)', () => {
      const ops: PatchOperation[] = [
        {
          op: PatchOperationType.DELETE_ELEMENT,
          targetId: 'card_main',
          proposedValue: {},
          reason: 'Delete main container'
        }
      ];

      engine.generateCheckoutCtaProposal();
      (engine as any).activeProposal.operations = ops;

      const validation = engine.validateActiveProposal();
      expect(validation.valid).toBe(false);
      expect(validation.errors.join(' ')).toContain('PROTECTED ELEMENT VIOLATION');
    });
  });

  // --- AUDIT LOGGER & EXPIRATION TESTS ---
  describe('Audit Logging & Proposal Expiration', () => {
    it('records structured audit records for lifecycle events', () => {
      engine.generateCheckoutCtaProposal();
      const approveRes = engine.approveProposal();
      engine.acceptAndExecuteProposal(approveRes.token!.token);

      const auditRecords = AuditLogger.getRecords();
      expect(auditRecords.length).toBeGreaterThan(0);

      const eventTypes = auditRecords.map(r => r.eventType);
      expect(eventTypes).toContain(AuditEventType.PROPOSAL_CREATED);
      expect(eventTypes).toContain(AuditEventType.PROPOSAL_APPROVED);
      expect(eventTypes).toContain(AuditEventType.EXECUTION_STARTED);
      expect(eventTypes).toContain(AuditEventType.VERIFICATION_PASSED);
    });

    it('flags proposals exceeding PROPOSAL_EXPIRATION_MS as EXPIRED', () => {
      const prop = engine.generateCheckoutCtaProposal();

      // Backdate creation timestamp by 6 minutes (360,000 ms)
      prop.createdAt = Date.now() - 360000;
      (engine as any).activeProposal = prop;

      const validation = engine.validateActiveProposal();
      expect(validation.valid).toBe(false);
      expect(validation.isExpired).toBe(true);
      expect(engine.getActiveProposal()?.status).toBe(ProposalStatus.EXPIRED);
    });
  });
});
