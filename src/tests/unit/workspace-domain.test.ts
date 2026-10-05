import { describe, it, expect, beforeEach } from 'vitest';
import { WorkspaceModel } from '../../core/domain/workspace/workspace-model';
import { createCheckoutInitialScene } from '../../core/domain/workspace/checkout-scene';
import { PatchOperationType, PatchOperation } from '../../core/domain/workspace/types';
import { ProposalEngine } from '../../core/domain/proposal/proposal-engine';
import { ProposalStatus } from '../../core/domain/proposal/types';

describe('Phase 2 — Workspace Domain & Proposal Engine Unit Tests', () => {
  let model: WorkspaceModel;
  let engine: ProposalEngine;

  beforeEach(() => {
    model = new WorkspaceModel(createCheckoutInitialScene());
    engine = new ProposalEngine(model);
  });

  // --- WORKSPACE TESTS ---
  describe('Workspace Operations', () => {
    it('creates a new element successfully', () => {
      const op: PatchOperation = {
        op: PatchOperationType.CREATE_ELEMENT,
        targetId: 'btn_new',
        proposedValue: {
          id: 'btn_new',
          type: 'button',
          x: 100,
          y: 100,
          w: 120,
          h: 40,
          label: 'New Action',
          style: { fill: '#10B981' }
        },
        reason: 'Add new action button'
      };

      const result = model.applyPatch([op]);
      expect(result.success).toBe(true);
      expect(model.getElement('btn_new')).toBeDefined();
      expect(model.getElement('btn_new')?.label).toBe('New Action');
      expect(model.getRevision()).toBe(2);
    });

    it('updates an existing element', () => {
      const op: PatchOperation = {
        op: PatchOperationType.UPDATE_ELEMENT,
        targetId: 'btn_pay',
        proposedValue: {
          w: 300,
          label: 'Pay Now (Updated)'
        },
        reason: 'Update CTA width and text'
      };

      const result = model.applyPatch([op]);
      expect(result.success).toBe(true);
      expect(model.getElement('btn_pay')?.w).toBe(300);
      expect(model.getElement('btn_pay')?.label).toBe('Pay Now (Updated)');
    });

    it('deletes an element', () => {
      const op: PatchOperation = {
        op: PatchOperationType.DELETE_ELEMENT,
        targetId: 'inp_coupon',
        proposedValue: {},
        reason: 'Remove coupon input'
      };

      const result = model.applyPatch([op]);
      expect(result.success).toBe(true);
      expect(model.getElement('inp_coupon')).toBeUndefined();
    });

    it('fails when operation targets a nonexistent element', () => {
      const op: PatchOperation = {
        op: PatchOperationType.UPDATE_STYLE,
        targetId: 'nonexistent_id',
        proposedValue: { fill: '#FF0000' },
        reason: 'Style update on missing element'
      };

      const result = model.applyPatch([op]);
      expect(result.success).toBe(false);
      expect(result.error).toContain('not found');
      expect(model.getRevision()).toBe(1); // Revision unchanged
    });
  });

  // --- PROPOSAL & STALE REVISION TESTS ---
  describe('Proposal Validation & Stale Detection', () => {
    it('generates a valid initial proposal', () => {
      const prop = engine.generateCheckoutCtaProposal();
      expect(prop).toBeDefined();
      expect(prop.status).toBe(ProposalStatus.PENDING);
      expect(prop.operations.length).toBe(2);

      const validation = engine.validateActiveProposal();
      expect(validation.valid).toBe(true);
      expect(validation.isStale).toBe(false);
    });

    it('detects STALE proposals when workspace revision increments', () => {
      // 1. Generate proposal against Revision 1
      const prop = engine.generateCheckoutCtaProposal();
      expect(prop.baseRevision).toBe(1);

      // 2. Perform manual mutation on workspace -> Revision 2
      model.applyPatch([{
        op: PatchOperationType.MOVE_ELEMENT,
        targetId: 'btn_pay',
        proposedValue: { x: 50, y: 260 },
        reason: 'Manual drag edit by human'
      }]);

      expect(model.getRevision()).toBe(2);

      // 3. Validate proposal -> Should be flagged STALE
      const validation = engine.validateActiveProposal();
      expect(validation.valid).toBe(false);
      expect(validation.isStale).toBe(true);
      expect(engine.getActiveProposal()?.status).toBe(ProposalStatus.STALE);
    });

    it('PREVENTS execution of stale proposals', () => {
      engine.generateCheckoutCtaProposal();
      engine.approveProposal();

      // Mutate workspace to increment revision
      model.applyPatch([{
        op: PatchOperationType.UPDATE_TEXT,
        targetId: 'txt_header',
        proposedValue: { label: 'Updated Header' },
        reason: 'Manual edit'
      }]);

      // Attempt accept and execute
      const result = engine.acceptAndExecuteProposal();
      expect(result.success).toBe(false);
      expect(result.error).toContain('STALE PROPOSAL');
    });
  });

  // --- HUMAN CONTROL & EXECUTION TESTS ---
  describe('Human Control & Closed-Loop Verification', () => {
    it('executes and verifies an ACCEPTED proposal', () => {
      engine.generateCheckoutCtaProposal();
      engine.approveProposal();

      const result = engine.acceptAndExecuteProposal();
      expect(result.success).toBe(true);
      expect(result.verification?.verified).toBe(true);
      expect(engine.getActiveProposal()?.status).toBe(ProposalStatus.VERIFIED);

      // Inspect updated domain model
      const updatedBtn = model.getElement('btn_pay');
      expect(updatedBtn?.w).toBe(320);
      expect(updatedBtn?.style.fill).toBe('#06B6D4');
      expect(model.getRevision()).toBe(2);
    });

    it('does NOT mutate workspace when REJECTED', () => {
      engine.generateCheckoutCtaProposal();

      const ok = engine.rejectProposal('Not needed');
      expect(ok).toBe(true);
      expect(engine.getActiveProposal()?.status).toBe(ProposalStatus.REJECTED);

      // Attempt to execute rejected proposal
      const execResult = engine.acceptAndExecuteProposal();
      expect(execResult.success).toBe(false);

      // Verify workspace remained untouched
      expect(model.getElement('btn_pay')?.w).toBe(180);
      expect(model.getRevision()).toBe(1);
    });

    it('supports MODIFY before execution', () => {
      const prop = engine.generateCheckoutCtaProposal();

      const modifiedOps = [...prop.operations];
      modifiedOps[0] = {
        ...modifiedOps[0],
        proposedValue: {
          ...modifiedOps[0].proposedValue,
          w: 280 // Modified width preference
        }
      };

      const modOk = engine.modifyProposal(modifiedOps);
      expect(modOk).toBe(true);
      expect(engine.getActiveProposal()?.status).toBe(ProposalStatus.MODIFIED);

      engine.approveProposal();

      // Execute modified proposal
      const execResult = engine.acceptAndExecuteProposal();
      expect(execResult.success).toBe(true);
      expect(model.getElement('btn_pay')?.w).toBe(280);
    });
  });
});
