export interface VersionViewCallbacks {
  onCreateBranch: (name: string, fromVersionId?: string) => Promise<void>;
  onSwitchBranch: (branchId: string) => Promise<void>;
  onCheckoutVersion: (versionId: string) => Promise<void>;
  onRollbackVersion: (versionId: string) => Promise<void>;
  onDiffVersions: (vIdA: string, vIdB: string) => Promise<void>;
  onCommitDirty: (message: string) => Promise<void>;
  onDiscardDirty: () => Promise<void>;
}

export class VersionView {
  constructor(
    private container: HTMLElement,
    private callbacks: VersionViewCallbacks
  ) {}

  public render(
    history: any[],
    branches: any[],
    activeBranchId: string,
    currentVersionId: string,
    isDirty: boolean = false,
    activeDiff?: any
  ): void {
    const activeBranch = branches.find(b => b.id === activeBranchId) || { name: 'main' };

    this.container.innerHTML = `
      <div class="version-panel" style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 12px; margin-top: 10px; font-family: sans-serif; color: #E2E8F0;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 8px; margin-bottom: 12px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-weight: 700; color: #38BDF8; font-size: 13px;">🌿 VERSION GRAPH</span>
            <span style="background: rgba(56, 189, 248, 0.2); color: #38BDF8; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">
              Branch: ${activeBranch.name}
            </span>
            ${isDirty ? '<span style="background: rgba(245, 158, 11, 0.2); color: #F59E0B; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700;">DIRTY</span>' : '<span style="background: rgba(16, 185, 129, 0.2); color: #10B981; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">CLEAN</span>'}
          </div>
          <div style="display: flex; gap: 6px;">
            <select id="branch-select" style="background: #1E293B; color: #E2E8F0; border: 1px solid #334155; border-radius: 4px; padding: 3px 6px; font-size: 11px;">
              ${branches.map(b => `<option value="${b.id}" ${b.id === activeBranchId ? 'selected' : ''}>${b.name} (${b.id.substring(0, 8)})</option>`).join('')}
            </select>
            <button id="btn-new-branch" style="background: #3B82F6; color: white; border: none; border-radius: 4px; padding: 3px 8px; font-size: 11px; cursor: pointer; font-weight: 600;">+ New Branch</button>
          </div>
        </div>

        ${isDirty ? `
          <div style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.4); padding: 8px; border-radius: 6px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 11px; color: #FCD34D;">Uncommitted manual edits in workspace.</span>
            <div style="display: flex; gap: 6px;">
              <button id="btn-commit-dirty" style="background: #10B981; color: white; border: none; border-radius: 4px; padding: 3px 8px; font-size: 11px; cursor: pointer;">Commit Edits</button>
              <button id="btn-discard-dirty" style="background: #EF4444; color: white; border: none; border-radius: 4px; padding: 3px 8px; font-size: 11px; cursor: pointer;">Discard</button>
            </div>
          </div>
        ` : ''}

        <div class="version-history-list" style="max-height: 180px; overflow-y: auto; display: flex; flex-direction: column; gap: 6px;">
          ${history.slice().reverse().map(v => {
            const isHead = v.id === currentVersionId;
            const authorBg = v.author === 'AI_ASSISTED' ? 'rgba(168, 85, 247, 0.2)' : 'rgba(59, 130, 246, 0.2)';
            const authorColor = v.author === 'AI_ASSISTED' ? '#C084FC' : '#60A5FA';
            const typeBadge = v.type === 'ROLLBACK' ? '<span style="background: rgba(239, 68, 68, 0.2); color: #FCA5A5; padding: 1px 5px; border-radius: 3px; font-size: 9px; margin-left: 4px;">ROLLBACK</span>' : '';

            return `
              <div style="background: ${isHead ? 'rgba(56, 189, 248, 0.1)' : '#1E293B'}; border: 1px solid ${isHead ? '#38BDF8' : '#334155'}; border-radius: 6px; padding: 8px; font-size: 11px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <div style="display: flex; align-items: center; gap: 6px;">
                    <span style="font-weight: 700; color: #F8FAFC;">Rev ${v.revision}</span>
                    <span style="color: #94A3B8; font-family: monospace; font-size: 10px;">${v.id.substring(0, 10)}</span>
                    <span style="background: ${authorBg}; color: ${authorColor}; padding: 1px 5px; border-radius: 3px; font-size: 10px; font-weight: 600;">${v.author}</span>
                    ${typeBadge}
                    ${isHead ? '<span style="background: #38BDF8; color: #0F172A; padding: 1px 5px; border-radius: 3px; font-size: 9px; font-weight: 800;">HEAD</span>' : ''}
                  </div>
                  <span style="color: #64748B; font-size: 10px;">${new Date(v.timestamp).toLocaleTimeString()}</span>
                </div>
                <div style="color: #CBD5E1; margin: 4px 0; font-size: 11px;">${v.message}</div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px; pt-4; border-top: 1px dashed rgba(255, 255, 255, 0.05);">
                  <span style="color: #64748B; font-family: monospace; font-size: 9px;">Hash: ${v.stateHash ? v.stateHash.substring(0, 12) : 'N/A'}...</span>
                  <div style="display: flex; gap: 4px;">
                    <button class="btn-diff-ver" data-id="${v.id}" style="background: #334155; color: #94A3B8; border: none; border-radius: 3px; padding: 2px 6px; font-size: 10px; cursor: pointer;">Diff</button>
                    ${!isHead ? `
                      <button class="btn-checkout-ver" data-id="${v.id}" style="background: #0D9488; color: white; border: none; border-radius: 3px; padding: 2px 6px; font-size: 10px; cursor: pointer;">Checkout</button>
                      <button class="btn-rollback-ver" data-id="${v.id}" style="background: #DC2626; color: white; border: none; border-radius: 3px; padding: 2px 6px; font-size: 10px; cursor: pointer;">Rollback</button>
                    ` : ''}
                  </div>
                </div>
              </div>
            `;
          }).join('')}
        </div>

        ${activeDiff ? `
          <div style="background: #0F172A; border: 1px solid #38BDF8; padding: 8px; border-radius: 6px; margin-top: 10px; font-size: 11px;">
            <div style="font-weight: 700; color: #38BDF8; margin-bottom: 4px;">Version Diff (${activeDiff.versionA.substring(0, 8)} ➔ ${activeDiff.versionB.substring(0, 8)})</div>
            <div>Added: ${activeDiff.added.length}, Removed: ${activeDiff.removed.length}, Modified: ${activeDiff.modified.length}, Moved: ${activeDiff.moved.length}</div>
          </div>
        ` : ''}
      </div>
    `;

    this.bindEvents(history, currentVersionId);
  }

  private bindEvents(history: any[], currentVersionId: string): void {
    const branchSelect = this.container.querySelector('#branch-select') as HTMLSelectElement;
    if (branchSelect) {
      branchSelect.addEventListener('change', async () => {
        await this.callbacks.onSwitchBranch(branchSelect.value);
      });
    }

    const btnNewBranch = this.container.querySelector('#btn-new-branch');
    if (btnNewBranch) {
      btnNewBranch.addEventListener('click', async () => {
        const name = prompt('Enter new branch name:');
        if (name && name.trim()) {
          await this.callbacks.onCreateBranch(name.trim());
        }
      });
    }

    const btnCommitDirty = this.container.querySelector('#btn-commit-dirty');
    if (btnCommitDirty) {
      btnCommitDirty.addEventListener('click', async () => {
        const msg = prompt('Enter commit message for manual edits:', 'User manual workspace edits');
        if (msg) await this.callbacks.onCommitDirty(msg);
      });
    }

    const btnDiscardDirty = this.container.querySelector('#btn-discard-dirty');
    if (btnDiscardDirty) {
      btnDiscardDirty.addEventListener('click', async () => {
        if (confirm('Discard uncommitted workspace changes?')) {
          await this.callbacks.onDiscardDirty();
        }
      });
    }

    this.container.querySelectorAll('.btn-diff-ver').forEach(btn => {
      btn.addEventListener('click', async () => {
        const targetId = (btn as HTMLElement).dataset.id!;
        await this.callbacks.onDiffVersions(targetId, currentVersionId);
      });
    });

    this.container.querySelectorAll('.btn-checkout-ver').forEach(btn => {
      btn.addEventListener('click', async () => {
        const targetId = (btn as HTMLElement).dataset.id!;
        await this.callbacks.onCheckoutVersion(targetId);
      });
    });

    this.container.querySelectorAll('.btn-rollback-ver').forEach(btn => {
      btn.addEventListener('click', async () => {
        const targetId = (btn as HTMLElement).dataset.id!;
        if (confirm(`Rollback workspace state to version ${targetId.substring(0, 8)}? (History will remain intact)`)) {
          await this.callbacks.onRollbackVersion(targetId);
        }
      });
    });
  }
}
