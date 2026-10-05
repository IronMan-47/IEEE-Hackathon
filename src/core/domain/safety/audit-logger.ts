export enum AuditEventType {
  PROPOSAL_CREATED = 'PROPOSAL_CREATED',
  PROPOSAL_VALIDATED = 'PROPOSAL_VALIDATED',
  PROPOSAL_MODIFIED = 'PROPOSAL_MODIFIED',
  PROPOSAL_REJECTED = 'PROPOSAL_REJECTED',
  PROPOSAL_APPROVED = 'PROPOSAL_APPROVED',
  EXECUTION_STARTED = 'EXECUTION_STARTED',
  EXECUTION_COMPLETED = 'EXECUTION_COMPLETED',
  VERIFICATION_PASSED = 'VERIFICATION_PASSED',
  VERIFICATION_FAILED = 'VERIFICATION_FAILED',
  PROPOSAL_STALE = 'PROPOSAL_STALE',
  EXECUTION_BLOCKED = 'EXECUTION_BLOCKED',
  EMERGENCY_STOP = 'EMERGENCY_STOP',
  VERSION_CREATED = 'VERSION_CREATED',
  BRANCH_CREATED = 'BRANCH_CREATED',
  BRANCH_SWITCHED = 'BRANCH_SWITCHED',
  VERSION_CHECKED_OUT = 'VERSION_CHECKED_OUT',
  ROLLBACK_CREATED = 'ROLLBACK_CREATED',
  VERSION_DIFF_REQUESTED = 'VERSION_DIFF_REQUESTED',
  CONFLICT_DETECTED = 'CONFLICT_DETECTED',
  UNCOMMITTED_CHANGES_BLOCKED = 'UNCOMMITTED_CHANGES_BLOCKED',
  INTEGRITY_CHECK_FAILED = 'INTEGRITY_CHECK_FAILED'
}

export interface AuditRecord {
  timestamp: number;
  eventType: AuditEventType;
  proposalId: string;
  workspaceId: string;
  revision: number;
  source: string;
  result: string;
  details?: Record<string, unknown>;
}

export class AuditLogger {
  private static records: AuditRecord[] = [];

  public static logEvent(
    eventType: AuditEventType,
    proposalId: string,
    workspaceId: string,
    revision: number,
    source: string,
    result: string,
    details?: Record<string, unknown>
  ): AuditRecord {
    const record: AuditRecord = {
      timestamp: Date.now(),
      eventType,
      proposalId,
      workspaceId,
      revision,
      source,
      result,
      details
    };

    AuditLogger.records.push(record);
    console.log(`[AUDIT] [${new Date(record.timestamp).toISOString()}] [${record.eventType}] Proposal: ${record.proposalId} | Rev: ${record.revision} | Result: ${record.result}`);
    return record;
  }

  public static getRecords(): AuditRecord[] {
    return [...AuditLogger.records];
  }

  public static clear(): void {
    AuditLogger.records = [];
  }
}
