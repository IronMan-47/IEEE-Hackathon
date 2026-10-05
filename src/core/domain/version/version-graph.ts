import { WorkspaceState, PatchOperation, InverseOperation, PatchOperationType } from '../workspace/types';
import { WorkspaceVersion, WorkspaceBranch, VersionAuthor, VersionDiffResult } from './types';
import { CanonicalHash } from './canonical-hash';
import { StateReconstructor } from './state-reconstructor';
import { DiffEngine } from './diff-engine';
import { VersionStore, VersionGraphSerialized } from './persistence';
import { AuditLogger, AuditEventType } from '../safety/audit-logger';

export class VersionGraphManager {
  private versions: Map<string, WorkspaceVersion> = new Map();
  private branches: Map<string, WorkspaceBranch> = new Map();
  private activeBranchId: string = '';
  private currentVersionId: string = '';
  private isDirty: boolean = false;
  private uncommittedOps: PatchOperation[] = [];
  private store: VersionStore;
  private isSystemReadyCallback: () => boolean;

  constructor(
    storePath?: string,
    isSystemReadyCallback?: () => boolean
  ) {
    this.store = new VersionStore(storePath);
    this.isSystemReadyCallback = isSystemReadyCallback || (() => true);
    this.loadFromStore();
  }

  public isReady(): boolean {
    return this.isSystemReadyCallback();
  }

  public getIsDirty(): boolean {
    return this.isDirty;
  }

  public getActiveBranchId(): string {
    return this.activeBranchId;
  }

  public getCurrentVersionId(): string {
    return this.currentVersionId;
  }

  public getVersion(versionId: string): WorkspaceVersion | undefined {
    const v = this.versions.get(versionId);
    return v ? JSON.parse(JSON.stringify(v)) : undefined;
  }

  public getBranch(branchId: string): WorkspaceBranch | undefined {
    const b = this.branches.get(branchId);
    return b ? JSON.parse(JSON.stringify(b)) : undefined;
  }

  public getAllBranches(): WorkspaceBranch[] {
    return Array.from(this.branches.values()).map(b => JSON.parse(JSON.stringify(b)));
  }

  /**
   * Initializes workspace root version (V0) if not already initialized.
   */
  public initRootVersion(workspaceId: string, initialState: WorkspaceState): WorkspaceVersion {
    if (this.versions.size > 0 && this.currentVersionId) {
      const existing = this.versions.get(this.currentVersionId);
      if (existing) return JSON.parse(JSON.stringify(existing));
    }

    const rootStateHash = CanonicalHash.hashState(initialState);
    const rootVersionId = `v_0_${workspaceId}`;
    const mainBranchId = `b_main_${workspaceId}`;

    const rootVersion: WorkspaceVersion = {
      id: rootVersionId,
      workspaceId,
      parentVersionId: null,
      branchId: mainBranchId,
      revision: initialState.revision || 0,
      timestamp: Date.now(),
      author: 'HUMAN',
      type: 'INITIAL',
      operations: [],
      inverseOperations: [],
      stateHash: rootStateHash,
      message: 'Initial workspace root version (V0)',
      snapshotState: JSON.parse(JSON.stringify(initialState))
    };

    const mainBranch: WorkspaceBranch = {
      id: mainBranchId,
      workspaceId,
      name: 'main',
      headVersionId: rootVersionId,
      createdFromVersionId: rootVersionId,
      createdAt: Date.now(),
      status: 'ACTIVE'
    };

    this.versions.set(rootVersion.id, rootVersion);
    this.branches.set(mainBranch.id, mainBranch);
    this.activeBranchId = mainBranch.id;
    this.currentVersionId = rootVersion.id;
    this.isDirty = false;
    this.uncommittedOps = [];

    AuditLogger.logEvent(
      AuditEventType.VERSION_CREATED,
      rootVersion.id,
      workspaceId,
      rootVersion.revision,
      'HUMAN',
      'CREATED',
      { isRoot: true, branchId: mainBranch.id }
    );

    AuditLogger.logEvent(
      AuditEventType.BRANCH_CREATED,
      mainBranch.id,
      workspaceId,
      rootVersion.revision,
      'HUMAN',
      'CREATED',
      { name: 'main', headVersionId: rootVersion.id }
    );

    this.persist();
    return JSON.parse(JSON.stringify(rootVersion));
  }

  /**
   * Commits a new immutable version to the version graph.
   */
  public commitVersion(options: {
    workspaceId: string;
    parentVersionId?: string;
    branchId?: string;
    operations: PatchOperation[];
    inverseOperations: InverseOperation[];
    state: WorkspaceState;
    author: VersionAuthor;
    proposalId?: string;
    message: string;
    type?: 'MUTATION' | 'ROLLBACK';
    sourceVersionId?: string;
  }): WorkspaceVersion {
    // 1. Emergency Stop Barrier
    if (!this.isSystemReadyCallback()) {
      AuditLogger.logEvent(
        AuditEventType.EXECUTION_BLOCKED,
        'N/A',
        options.workspaceId,
        options.state.revision,
        'VERSION_GRAPH',
        'BLOCKED',
        { reason: 'Emergency Stop is active' }
      );
      throw new Error('EMERGENCY_STOP_BLOCKED: System is in STOPPED state; version commits are prohibited.');
    }

    const parentId = options.parentVersionId || this.currentVersionId;
    const targetBranchId = options.branchId || this.activeBranchId;

    if (!parentId && this.versions.size > 0) {
      throw new Error('Invariant Violation: Every non-root version must have a valid parentVersionId');
    }

    const branch = this.branches.get(targetBranchId);
    if (!branch) {
      throw new Error(`Target branch [ ${targetBranchId} ] not found`);
    }

    const stateHash = CanonicalHash.hashState(options.state);
    const newVersionId = `v_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;

    const newVersion: WorkspaceVersion = {
      id: newVersionId,
      workspaceId: options.workspaceId,
      parentVersionId: parentId || null,
      branchId: targetBranchId,
      revision: options.state.revision,
      timestamp: Date.now(),
      proposalId: options.proposalId,
      author: options.author,
      type: options.type || 'MUTATION',
      sourceVersionId: options.sourceVersionId,
      operations: JSON.parse(JSON.stringify(options.operations)),
      inverseOperations: JSON.parse(JSON.stringify(options.inverseOperations)),
      stateHash,
      message: options.message,
      snapshotState: JSON.parse(JSON.stringify(options.state))
    };

    // Immutability Check: ensure ID doesn't conflict
    if (this.versions.has(newVersion.id)) {
      throw new Error(`Duplicate commit blocked: Version ${newVersion.id} already exists`);
    }

    this.versions.set(newVersion.id, newVersion);

    // Update branch head
    branch.headVersionId = newVersion.id;
    this.branches.set(branch.id, branch);

    this.currentVersionId = newVersion.id;
    this.activeBranchId = targetBranchId;
    this.isDirty = false;
    this.uncommittedOps = [];

    AuditLogger.logEvent(
      AuditEventType.VERSION_CREATED,
      newVersion.id,
      options.workspaceId,
      newVersion.revision,
      options.author,
      'COMMITTED',
      {
        parentVersionId: parentId,
        branchId: targetBranchId,
        type: newVersion.type,
        message: newVersion.message,
        stateHash
      }
    );

    this.persist();
    return JSON.parse(JSON.stringify(newVersion));
  }

  /**
   * Creates a new branch starting from a specific version or current head.
   */
  public createBranch(name: string, fromVersionId?: string): WorkspaceBranch {
    if (!this.isSystemReadyCallback()) {
      throw new Error('EMERGENCY_STOP_BLOCKED: Cannot create branch in STOPPED state');
    }

    const targetVersionId = fromVersionId || this.currentVersionId;
    const targetVersion = this.versions.get(targetVersionId);
    if (!targetVersion) {
      throw new Error(`Source version [ ${targetVersionId} ] not found for branching`);
    }

    // Check duplicate branch name
    const existing = Array.from(this.branches.values()).find(b => b.name === name);
    if (existing) {
      throw new Error(`Branch with name [ ${name} ] already exists`);
    }

    const newBranchId = `b_${name}_${Date.now()}`;
    const newBranch: WorkspaceBranch = {
      id: newBranchId,
      workspaceId: targetVersion.workspaceId,
      name,
      headVersionId: targetVersion.id,
      createdFromVersionId: targetVersion.id,
      createdAt: Date.now(),
      status: 'ACTIVE'
    };

    this.branches.set(newBranch.id, newBranch);

    AuditLogger.logEvent(
      AuditEventType.BRANCH_CREATED,
      newBranch.id,
      targetVersion.workspaceId,
      targetVersion.revision,
      'HUMAN',
      'CREATED',
      { name, headVersionId: targetVersion.id }
    );

    this.persist();
    return JSON.parse(JSON.stringify(newBranch));
  }

  /**
   * Switches active branch, reconstructing head workspace state.
   * Safety Guard: Blocks switch if workspace is DIRTY (uncommitted changes).
   */
  public checkoutBranch(branchId: string, options?: { force?: boolean }): WorkspaceState {
    const targetBranch = this.branches.get(branchId);
    if (!targetBranch) {
      throw new Error(`Target branch [ ${branchId} ] not found`);
    }

    if (this.isDirty && !options?.force) {
      AuditLogger.logEvent(
        AuditEventType.UNCOMMITTED_CHANGES_BLOCKED,
        this.currentVersionId,
        targetBranch.workspaceId,
        0,
        'USER',
        'BLOCKED',
        { targetBranchId: branchId }
      );
      throw new Error('UNCOMMITTED_CHANGES_BLOCKED: Active workspace has uncommitted changes. Commit or discard changes before switching branches.');
    }

    const headVersion = this.versions.get(targetBranch.headVersionId);
    if (!headVersion) {
      throw new Error(`Head version [ ${targetBranch.headVersionId} ] not found for branch ${branchId}`);
    }

    const reconstructedState = StateReconstructor.reconstructState(headVersion, this.versions);

    this.activeBranchId = targetBranch.id;
    this.currentVersionId = headVersion.id;
    this.isDirty = false;
    this.uncommittedOps = [];

    AuditLogger.logEvent(
      AuditEventType.BRANCH_SWITCHED,
      headVersion.id,
      targetBranch.workspaceId,
      headVersion.revision,
      'HUMAN',
      'SWITCHED',
      { branchId, headVersionId: headVersion.id }
    );

    this.persist();
    return reconstructedState;
  }

  /**
   * Checks out a specific historical version.
   * Safety Guard: Blocks checkout if workspace is DIRTY.
   */
  public checkoutVersion(versionId: string, options?: { force?: boolean }): WorkspaceState {
    const version = this.versions.get(versionId);
    if (!version) {
      throw new Error(`Target version [ ${versionId} ] not found`);
    }

    if (this.isDirty && !options?.force) {
      AuditLogger.logEvent(
        AuditEventType.UNCOMMITTED_CHANGES_BLOCKED,
        this.currentVersionId,
        version.workspaceId,
        0,
        'USER',
        'BLOCKED',
        { targetVersionId: versionId }
      );
      throw new Error('UNCOMMITTED_CHANGES_BLOCKED: Active workspace has uncommitted changes. Commit or discard changes before checking out version.');
    }

    const reconstructedState = StateReconstructor.reconstructState(version, this.versions);

    this.currentVersionId = version.id;
    this.activeBranchId = version.branchId;
    this.isDirty = false;
    this.uncommittedOps = [];

    AuditLogger.logEvent(
      AuditEventType.VERSION_CHECKED_OUT,
      version.id,
      version.workspaceId,
      version.revision,
      'HUMAN',
      'CHECKED_OUT',
      { versionId }
    );

    this.persist();
    return reconstructedState;
  }

  /**
   * Rollback workspace state to a historical version.
   * CRITICAL INVARIANT: History is NEVER deleted. Rollback creates a NEW version node (V_new)
   * whose state matches target historical version.
   */
  public rollbackToVersion(
    targetVersionId: string,
    author: VersionAuthor = 'HUMAN',
    customMessage?: string
  ): { newVersion: WorkspaceVersion; state: WorkspaceState } {
    if (!this.isSystemReadyCallback()) {
      throw new Error('EMERGENCY_STOP_BLOCKED: Rollback is prohibited in STOPPED state');
    }

    const targetVersion = this.versions.get(targetVersionId);
    if (!targetVersion) {
      throw new Error(`Target version [ ${targetVersionId} ] not found for rollback`);
    }

    const currentHead = this.versions.get(this.currentVersionId);
    if (!currentHead) {
      throw new Error(`Current head version [ ${this.currentVersionId} ] not found`);
    }

    // Reconstruct exact state of target version
    const restoredState = StateReconstructor.reconstructState(targetVersion, this.versions);
    restoredState.revision = currentHead.revision + 1;
    restoredState.lastUpdated = Date.now();

    const diff = DiffEngine.diff(currentHead.snapshotState, restoredState);

    // Compute synthetic ops to transition current head state to target restored state
    const syntheticOps: PatchOperation[] = [];

    for (const rem of diff.removed) {
      syntheticOps.push({
        op: PatchOperationType.DELETE_ELEMENT,
        targetId: rem.id,
        proposedValue: {},
        reason: `Rollback: Delete element [ ${rem.id} ]`
      });
    }

    for (const add of diff.added) {
      syntheticOps.push({
        op: PatchOperationType.CREATE_ELEMENT,
        targetId: add.id,
        proposedValue: add as unknown as Record<string, unknown>,
        reason: `Rollback: Restore element [ ${add.id} ]`
      });
    }

    for (const mod of diff.modified) {
      syntheticOps.push({
        op: PatchOperationType.UPDATE_ELEMENT,
        targetId: mod.elementId,
        proposedValue: { [mod.property]: mod.newValue },
        reason: `Rollback: Restore property ${mod.property}`
      });
    }

    for (const mv of diff.moved) {
      syntheticOps.push({
        op: PatchOperationType.MOVE_ELEMENT,
        targetId: mv.elementId,
        proposedValue: { x: mv.newX, y: mv.newY },
        reason: `Rollback: Restore position (${mv.newX}, ${mv.newY})`
      });
    }

    const message = customMessage || `Rollback workspace state to version ${targetVersionId}`;

    const newVersion = this.commitVersion({
      workspaceId: targetVersion.workspaceId,
      parentVersionId: currentHead.id,
      branchId: this.activeBranchId,
      operations: syntheticOps,
      inverseOperations: [],
      state: restoredState,
      author,
      type: 'ROLLBACK',
      sourceVersionId: targetVersionId,
      message
    });

    AuditLogger.logEvent(
      AuditEventType.ROLLBACK_CREATED,
      newVersion.id,
      targetVersion.workspaceId,
      newVersion.revision,
      author,
      'ROLLBACK_SUCCESS',
      { restoredVersionId: targetVersionId, parentVersionId: currentHead.id }
    );

    return { newVersion, state: restoredState };
  }

  /**
   * Computes domain diff between two versions.
   */
  public diffVersions(versionIdA: string, versionIdB: string): VersionDiffResult {
    const vA = this.versions.get(versionIdA);
    const vB = this.versions.get(versionIdB);

    if (!vA || !vB) {
      throw new Error(`Invalid version ID(s) provided for diff: ${versionIdA}, ${versionIdB}`);
    }

    const stateA = StateReconstructor.reconstructState(vA, this.versions);
    const stateB = StateReconstructor.reconstructState(vB, this.versions);

    AuditLogger.logEvent(
      AuditEventType.VERSION_DIFF_REQUESTED,
      versionIdB,
      vA.workspaceId,
      vB.revision,
      'USER',
      'DIFF',
      { versionIdA, versionIdB }
    );

    return DiffEngine.diff(stateA, stateB, versionIdA, versionIdB);
  }

  /**
   * Tracks uncommitted user edits.
   */
  public markDirty(ops?: PatchOperation[]): void {
    this.isDirty = true;
    if (ops) {
      this.uncommittedOps.push(...ops);
    }
  }

  /**
   * Commits uncommitted dirty workspace changes as a human version.
   */
  public commitDirty(
    workspaceId: string,
    state: WorkspaceState,
    message: string = 'User manual workspace edits'
  ): WorkspaceVersion {
    return this.commitVersion({
      workspaceId,
      operations: this.uncommittedOps,
      inverseOperations: [],
      state,
      author: 'HUMAN',
      type: 'MUTATION',
      message
    });
  }

  /**
   * Discards dirty uncommitted changes and returns current head state.
   */
  public discardDirty(): WorkspaceState {
    this.isDirty = false;
    this.uncommittedOps = [];
    const headVersion = this.versions.get(this.currentVersionId);
    if (!headVersion) {
      throw new Error('Current head version missing');
    }
    return StateReconstructor.reconstructState(headVersion, this.versions);
  }

  /**
   * Gets version history lineage for the active branch or given branch.
   */
  public getHistory(branchId?: string): WorkspaceVersion[] {
    const targetBranchId = branchId || this.activeBranchId;
    const branch = this.branches.get(targetBranchId);
    if (!branch) return [];

    const lineage = StateReconstructor.getLineageFromRoot(branch.headVersionId, this.versions);
    return lineage.map(v => JSON.parse(JSON.stringify(v)));
  }

  public getFullGraph(): WorkspaceVersion[] {
    return Array.from(this.versions.values()).map(v => JSON.parse(JSON.stringify(v)));
  }

  private persist(): void {
    const serialized: VersionGraphSerialized = {
      workspaceId: this.versions.get(this.currentVersionId)?.workspaceId || 'checkout_demo',
      activeBranchId: this.activeBranchId,
      currentVersionId: this.currentVersionId,
      versions: Array.from(this.versions.values()),
      branches: Array.from(this.branches.values())
    };
    this.store.saveGraph(serialized);
  }

  private loadFromStore(): void {
    const data = this.store.loadGraph();
    if (!data) return;

    this.versions.clear();
    this.branches.clear();

    for (const v of data.versions) {
      this.versions.set(v.id, v);
    }
    for (const b of data.branches) {
      this.branches.set(b.id, b);
    }

    this.activeBranchId = data.activeBranchId;
    this.currentVersionId = data.currentVersionId;
    this.isDirty = false;
    this.uncommittedOps = [];
  }
}
