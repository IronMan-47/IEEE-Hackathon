import * as fs from 'fs';
import * as path from 'path';
import { WorkspaceVersion, WorkspaceBranch } from './types';
import { CanonicalHash } from './canonical-hash';
import { AuditLogger, AuditEventType } from '../safety/audit-logger';

export interface VersionGraphSerialized {
  workspaceId: string;
  activeBranchId: string;
  currentVersionId: string;
  versions: WorkspaceVersion[];
  branches: WorkspaceBranch[];
}

export class VersionStore {
  private filePath: string;

  constructor(filePath?: string) {
    if (filePath) {
      this.filePath = filePath;
    } else {
      const jarvisDir = path.join(process.cwd(), '.jarvis');
      if (!fs.existsSync(jarvisDir)) {
        fs.mkdirSync(jarvisDir, { recursive: true });
      }
      this.filePath = path.join(jarvisDir, 'workspace_history.json');
    }
  }

  public getFilePath(): string {
    return this.filePath;
  }

  /**
   * Saves version graph atomically using temporary file + rename strategy.
   * Guarantees crash safety.
   */
  public saveGraph(data: VersionGraphSerialized): void {
    const dir = path.dirname(this.filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    const tmpPath = `${this.filePath}.tmp.${Date.now()}`;
    const payload = JSON.stringify(data, null, 2);

    fs.writeFileSync(tmpPath, payload, 'utf-8');
    fs.renameSync(tmpPath, this.filePath);
  }

  /**
   * Loads version graph from local storage and verifies state integrity.
   */
  public loadGraph(): VersionGraphSerialized | null {
    if (!fs.existsSync(this.filePath)) {
      return null;
    }

    try {
      const raw = fs.readFileSync(this.filePath, 'utf-8');
      const data: VersionGraphSerialized = JSON.parse(raw);

      // Verify integrity of versions
      for (const v of data.versions) {
        const isValid = CanonicalHash.verifyStateHash(v.snapshotState, v.stateHash);
        if (!isValid) {
          AuditLogger.logEvent(
            AuditEventType.INTEGRITY_CHECK_FAILED,
            v.id,
            v.workspaceId,
            v.revision,
            'VERSION_STORE',
            'FAILED',
            { error: `Hash mismatch for version ${v.id}` }
          );
          throw new Error(`INTEGRITY_ERROR: Version ${v.id} state hash mismatch`);
        }
      }

      return data;
    } catch (err: unknown) {
      console.error('[VersionStore] Error loading history:', err);
      return null;
    }
  }

  public clear(): void {
    if (fs.existsSync(this.filePath)) {
      fs.unlinkSync(this.filePath);
    }
  }
}
