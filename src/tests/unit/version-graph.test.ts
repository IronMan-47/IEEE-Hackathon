import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import { VersionGraphManager } from '../../core/domain/version/version-graph';
import { CanonicalHash } from '../../core/domain/version/canonical-hash';
import { DiffEngine } from '../../core/domain/version/diff-engine';
import { WorkspaceState, PatchOperationType } from '../../core/domain/workspace/types';
import { createCheckoutInitialScene } from '../../core/domain/workspace/checkout-scene';
import { AuditLogger } from '../../core/domain/safety/audit-logger';

describe('Phase 5 — Version Graph, Branching & Rollback Unit Tests', () => {
  let tempStorePath: string;
  let manager: VersionGraphManager;
  let initialState: WorkspaceState;
  let isSystemReady: boolean;

  beforeEach(() => {
    AuditLogger.clear();
    tempStorePath = path.join(__dirname, `.temp_history_${Date.now()}_${Math.random().toString(36).substring(2, 6)}.json`);
    initialState = createCheckoutInitialScene();
    isSystemReady = true;
    manager = new VersionGraphManager(tempStorePath, () => isSystemReady);
    manager.initRootVersion('test_workspace', initialState);
  });

  afterEach(() => {
    if (fs.existsSync(tempStorePath)) {
      fs.unlinkSync(tempStorePath);
    }
  });

  describe('Root Version & Hashing Invariants', () => {
    it('creates V0 root version with canonical state hash', () => {
      const history = manager.getHistory();
      expect(history.length).toBe(1);

      const v0 = history[0];
      expect(v0.parentVersionId).toBeNull();
      expect(v0.author).toBe('HUMAN');
      expect(v0.type).toBe('INITIAL');
      expect(v0.stateHash).toBe(CanonicalHash.hashState(initialState));
      expect(v0.revision).toBe(initialState.revision);
    });

    it('enforces canonical hashing key-order independence', () => {
      const stateA: WorkspaceState = JSON.parse(JSON.stringify(initialState));
      const stateB: WorkspaceState = JSON.parse(JSON.stringify(initialState));

      // Rearrange keys in stateB elements
      const reorderedElements: any = {};
      Object.keys(stateB.elements).reverse().forEach(key => {
        reorderedElements[key] = stateB.elements[key];
      });
      stateB.elements = reorderedElements;

      const hashA = CanonicalHash.hashState(stateA);
      const hashB = CanonicalHash.hashState(stateB);

      expect(hashA).toBe(hashB);
    });

    it('detects state hash alteration when element property changes', () => {
      const stateA = JSON.parse(JSON.stringify(initialState));
      const stateB = JSON.parse(JSON.stringify(initialState));
      stateB.elements['btn_pay'].w = 999;

      const hashA = CanonicalHash.hashState(stateA);
      const hashB = CanonicalHash.hashState(stateB);

      expect(hashA).not.toBe(hashB);
    });
  });

  describe('Sequential Versioning & Immutability', () => {
    it('commits sequential versions and increments workspace revision', () => {
      const updatedState = JSON.parse(JSON.stringify(initialState));
      updatedState.revision += 1;
      updatedState.elements['btn_pay'].w = 320;

      const ops = [
        {
          op: PatchOperationType.RESIZE_ELEMENT,
          targetId: 'btn_pay',
          proposedValue: { w: 320 },
          reason: 'Enlarge pay CTA'
        }
      ];

      const v1 = manager.commitVersion({
        workspaceId: 'test_workspace',
        operations: ops,
        inverseOperations: [],
        state: updatedState,
        author: 'AI_ASSISTED',
        message: 'Enlarge pay CTA width to 320px'
      });

      expect(v1.parentVersionId).toBe(manager.getHistory()[0].id);
      expect(v1.author).toBe('AI_ASSISTED');
      expect(v1.revision).toBe(updatedState.revision);

      const history = manager.getHistory();
      expect(history.length).toBe(2);
    });

    it('prevents historical version mutation (Invariance of committed nodes)', () => {
      const history = manager.getHistory();
      const v0 = history[0];

      // Attempting to mutate returned version does not alter stored version
      (v0 as any).message = 'MUTATED MESSAGE';

      const refetched = manager.getVersion(v0.id);
      expect(refetched?.message).toBe('Initial workspace root version (V0)');
    });
  });

  describe('Branching Model & Divergence', () => {
    it('creates branches from current head and historical versions', () => {
      const b1 = manager.createBranch('experiment-1');
      expect(b1.name).toBe('experiment-1');
      expect(b1.headVersionId).toBe(manager.getCurrentVersionId());

      const allBranches = manager.getAllBranches();
      expect(allBranches.length).toBe(2); // main + experiment-1
    });

    it('allows independent branch progression without mutating sibling branches', () => {
      const rootHeadId = manager.getCurrentVersionId();

      // Create branch feature-a
      const bA = manager.createBranch('feature-a');
      manager.checkoutBranch(bA.id);

      // Commit V1 on feature-a
      const stateA = JSON.parse(JSON.stringify(initialState));
      stateA.revision += 1;
      stateA.elements['btn_pay'].label = 'Branch A Pay';

      manager.commitVersion({
        workspaceId: 'test_workspace',
        operations: [],
        inverseOperations: [],
        state: stateA,
        author: 'HUMAN',
        message: 'Update text on branch A'
      });

      const headA = manager.getCurrentVersionId();

      // Switch back to main
      const mainBranches = manager.getAllBranches().find(b => b.name === 'main')!;
      const stateMain = manager.checkoutBranch(mainBranches.id);

      expect(manager.getCurrentVersionId()).toBe(rootHeadId);
      expect(stateMain.elements['btn_pay'].label).not.toBe('Branch A Pay');
      expect(headA).not.toBe(rootHeadId);
    });
  });

  describe('Rollback & Non-Destructive History Guarantee', () => {
    it('performs rollback by creating a NEW version while preserving full history intact', () => {
      const v0Id = manager.getCurrentVersionId();

      // Commit V1
      const state1 = JSON.parse(JSON.stringify(initialState));
      state1.revision += 1;
      state1.elements['btn_pay'].w = 400;

      const v1 = manager.commitVersion({
        workspaceId: 'test_workspace',
        operations: [],
        inverseOperations: [],
        state: state1,
        author: 'AI_ASSISTED',
        message: 'Mutation 1'
      });

      // Commit V2
      const state2 = JSON.parse(JSON.stringify(state1));
      state2.revision += 1;
      state2.elements['card_summary'].y = 300;

      const v2 = manager.commitVersion({
        workspaceId: 'test_workspace',
        operations: [],
        inverseOperations: [],
        state: state2,
        author: 'HUMAN',
        message: 'Mutation 2'
      });

      expect(manager.getHistory().length).toBe(3); // V0, V1, V2

      // Rollback to V0
      const rollbackRes = manager.rollbackToVersion(v0Id, 'HUMAN', 'Rollback state to V0');

      const historyAfterRollback = manager.getHistory();
      expect(historyAfterRollback.length).toBe(4); // V0, V1, V2, V3(Rollback)

      const rollbackNode = historyAfterRollback[3];
      expect(rollbackNode.type).toBe('ROLLBACK');
      expect(rollbackNode.sourceVersionId).toBe(v0Id);
      expect(rollbackNode.parentVersionId).toBe(v2.id);
      expect(rollbackNode.stateHash).toBe(CanonicalHash.hashState(rollbackRes.state));
      expect(rollbackRes.state.elements['btn_pay'].w).toBe(initialState.elements['btn_pay'].w);
    });
  });

  describe('Diff Engine', () => {
    it('computes accurate domain diff between two workspace states', () => {
      const stateA = createCheckoutInitialScene();
      const stateB = JSON.parse(JSON.stringify(stateA));

      stateB.elements['btn_pay'].w = 320; // Modified
      stateB.elements['btn_pay'].x = 100; // Moved
      delete stateB.elements['btn_coupon']; // Removed
      stateB.elements['new_element'] = { id: 'new_element', type: 'text', x: 0, y: 0, w: 50, h: 50, label: 'New' }; // Added

      const diff = DiffEngine.diff(stateA, stateB, 'vA', 'vB');

      expect(diff.identical).toBe(false);
      expect(diff.added.length).toBe(1);
      expect(diff.added[0].id).toBe('new_element');
      expect(diff.removed.length).toBe(1);
      expect(diff.removed[0].id).toBe('btn_coupon');
      expect(diff.moved.length).toBe(1);
      expect(diff.moved[0].elementId).toBe('btn_pay');
      expect(diff.modified.length).toBe(1);
      expect(diff.modified[0].property).toBe('w');
    });
  });

  describe('Dirty State & Safety Controls', () => {
    it('blocks branch switching when active workspace state is DIRTY', () => {
      const branch2 = manager.createBranch('feature-b');
      manager.markDirty();

      expect(manager.getIsDirty()).toBe(true);

      expect(() => {
        manager.checkoutBranch(branch2.id);
      }).toThrow(/UNCOMMITTED_CHANGES_BLOCKED/);
    });

    it('allows committing dirty state as a HUMAN authored version', () => {
      const updatedState = JSON.parse(JSON.stringify(initialState));
      updatedState.revision += 1;
      updatedState.elements['card_summary'].x = 50;

      manager.markDirty();
      const dirtyCommit = manager.commitDirty('test_workspace', updatedState, 'Manual edit commit');

      expect(manager.getIsDirty()).toBe(false);
      expect(dirtyCommit.author).toBe('HUMAN');
      expect(dirtyCommit.message).toBe('Manual edit commit');
    });

    it('blocks workspace mutations when Emergency Stop is STOPPED', () => {
      isSystemReady = false; // Trigger STOPPED state

      const updatedState = JSON.parse(JSON.stringify(initialState));

      expect(() => {
        manager.commitVersion({
          workspaceId: 'test_workspace',
          operations: [],
          inverseOperations: [],
          state: updatedState,
          author: 'HUMAN',
          message: 'Should block'
        });
      }).toThrow(/EMERGENCY_STOP_BLOCKED/);

      expect(() => {
        manager.rollbackToVersion(manager.getCurrentVersionId());
      }).toThrow(/EMERGENCY_STOP_BLOCKED/);
    });
  });

  describe('Persistence & Crash Safety', () => {
    it('persists and restores version graph across manager reinstantiation', () => {
      // Commit V1
      const updatedState = JSON.parse(JSON.stringify(initialState));
      updatedState.revision += 1;
      updatedState.elements['btn_pay'].label = 'Persisted Label';

      const v1 = manager.commitVersion({
        workspaceId: 'test_workspace',
        operations: [],
        inverseOperations: [],
        state: updatedState,
        author: 'AI_ASSISTED',
        message: 'Persisted mutation'
      });

      // Instantiate a new manager pointing to same store file (simulating app restart)
      const restoredManager = new VersionGraphManager(tempStorePath, () => true);
      const restoredHistory = restoredManager.getHistory();

      expect(restoredHistory.length).toBe(2);
      expect(restoredManager.getCurrentVersionId()).toBe(v1.id);

      const headState = restoredManager.getVersion(v1.id)?.snapshotState;
      expect(headState?.elements['btn_pay'].label).toBe('Persisted Label');
    });
  });
});
