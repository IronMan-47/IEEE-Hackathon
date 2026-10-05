import { PatchOperation } from '../workspace/types';
import { OperationRiskLevel } from '../safety/safety-limits';

export enum ProposalStatus {
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
  MODIFIED = 'MODIFIED',
  EXECUTED = 'EXECUTED',
  VERIFIED = 'VERIFIED',
  FAILED = 'FAILED',
  STALE = 'STALE',
  EXPIRED = 'EXPIRED'
}

export interface Proposal {
  id: string;
  workspaceId: string;
  baseRevision: number;
  title: string;
  reason: string;
  operations: PatchOperation[];
  createdAt: number;
  source: 'AI' | 'HUMAN';
  status: ProposalStatus;
  statusReason?: string;

  // Phase 4 Metadata & Safety Additions
  modifiedFromId?: string;
  riskLevel?: OperationRiskLevel;
  isDestructive?: boolean;
  approvalToken?: string;
}
