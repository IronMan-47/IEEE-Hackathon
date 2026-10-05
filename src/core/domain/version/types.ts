import { WorkspaceState, WorkspaceElement, PatchOperation, InverseOperation } from '../workspace/types';

export type VersionAuthor = 'HUMAN' | 'AI_ASSISTED';
export type VersionType = 'MUTATION' | 'ROLLBACK' | 'INITIAL';
export type BranchStatus = 'ACTIVE' | 'ARCHIVED';

export interface WorkspaceVersion {
  id: string;
  workspaceId: string;
  parentVersionId: string | null;
  branchId: string;
  revision: number;
  timestamp: number;
  proposalId?: string;
  author: VersionAuthor;
  type: VersionType;
  sourceVersionId?: string; // Set when type === 'ROLLBACK'
  operations: PatchOperation[];
  inverseOperations: InverseOperation[];
  stateHash: string; // SHA-256 of canonical state
  message: string;
  snapshotState: WorkspaceState; // Stored canonical snapshot for 100% accurate reconstruction
}

export interface WorkspaceBranch {
  id: string;
  workspaceId: string;
  name: string;
  headVersionId: string;
  createdFromVersionId: string;
  createdAt: number;
  status: BranchStatus;
}

export interface PropertyDiff {
  elementId: string;
  property: string;
  oldValue: any;
  newValue: any;
}

export interface SpatialDiff {
  elementId: string;
  oldX?: number;
  oldY?: number;
  newX?: number;
  newY?: number;
}

export interface VersionDiffResult {
  versionA: string;
  versionB: string;
  added: WorkspaceElement[];
  removed: WorkspaceElement[];
  modified: PropertyDiff[];
  moved: SpatialDiff[];
  identical: boolean;
}
