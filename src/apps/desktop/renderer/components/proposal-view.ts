import { Proposal } from '../../../../core/domain/proposal/types';

export interface ProposalViewCallbacks {
  onAccept: () => void;
  onReject: () => void;
  onModify: (ops: any[]) => void;
  onSimulateStale: () => void;
  onGenerateAI: (userText?: string) => void;
}

export class ProposalView {
  constructor(private container: HTMLElement, private callbacks: ProposalViewCallbacks) {}

  public render(proposal: Proposal | null, currentRevision: number): void {
    this.container.innerHTML = '';

    const drawer = document.createElement('div');
    drawer.className = 'proposal-drawer';

    if (!proposal) {
      drawer.innerHTML = `
        <div class="no-proposal-card">
          <p class="no-prop-text">Natural Language Intent to Python Agent Core:</p>
          <div class="prompt-input-row">
            <input id="prompt-input" type="text" class="prompt-input-field" value="Make the Pay Now button more prominent" placeholder="Ask JARVIS to improve layout...">
            <button id="btn-generate-ai" class="ai-gen-btn">
              <span>✨</span> Propose
            </button>
          </div>
        </div>
      `;
      this.container.appendChild(drawer);
      document.getElementById('btn-generate-ai')?.addEventListener('click', () => {
        const inp = document.getElementById('prompt-input') as HTMLInputElement;
        const text = inp ? inp.value : 'Make the Pay Now button more prominent';
        this.callbacks.onGenerateAI(text);
      });
      return;
    }

    const isPending = proposal.status === 'PENDING' || proposal.status === 'MODIFIED';
    const isStale = proposal.status === 'STALE';
    const isVerified = proposal.status === 'VERIFIED';
    const isRejected = proposal.status === 'REJECTED';

    drawer.innerHTML = `
      <div class="proposal-card status-${proposal.status.toLowerCase()}">
        <div class="prop-header">
          <div class="prop-title-row">
            <span class="prop-source-badge">${proposal.source}</span>
            <span class="prop-title">${proposal.title}</span>
          </div>
          <span class="status-badge status-${proposal.status.toLowerCase()}">${proposal.status}</span>
        </div>

        <p class="prop-reason">${proposal.reason}</p>

        <div class="revision-info">
          <span>Base Revision: Rev ${proposal.baseRevision}</span>
          <span>Current Workspace: Rev ${currentRevision}</span>
        </div>

        <!-- Diff Inspector -->
        <div class="diff-inspector">
          <div class="diff-header">Structured Patch Diff</div>
          <div class="diff-list">
            ${proposal.operations.map(op => `
              <div class="diff-item">
                <span class="diff-op">${op.op}</span>
                <span class="diff-target">[ ${op.targetId} ]</span>
                <p class="diff-reason">${op.reason}</p>
              </div>
            `).join('')}
          </div>
        </div>

        ${proposal.statusReason ? `
          <div class="status-reason-banner">
            ⚠️ ${proposal.statusReason}
          </div>
        ` : ''}

        <!-- Human Action Controls -->
        <div class="human-controls">
          ${isPending ? `
            <button id="btn-accept-prop" class="btn-accept">✓ Accept Proposal</button>
            <button id="btn-modify-prop" class="btn-modify">✏️ Modify</button>
            <button id="btn-reject-prop" class="btn-reject">✕ Reject</button>
            <button id="btn-simulate-stale" class="btn-stale" title="Simulate workspace edit while proposal is pending">⚡ Simulate Stale Edit</button>
          ` : `
            <button id="btn-generate-new-ai" class="ai-gen-btn">
              <span>✨</span> Generate New Proposal
            </button>
          `}
        </div>
      </div>
    `;

    this.container.appendChild(drawer);

    // Event listeners
    document.getElementById('btn-accept-prop')?.addEventListener('click', () => this.callbacks.onAccept());
    document.getElementById('btn-reject-prop')?.addEventListener('click', () => this.callbacks.onReject());
    document.getElementById('btn-simulate-stale')?.addEventListener('click', () => this.callbacks.onSimulateStale());
    document.getElementById('btn-generate-new-ai')?.addEventListener('click', () => this.callbacks.onGenerateAI());

    document.getElementById('btn-modify-prop')?.addEventListener('click', () => {
      // Prompt user to modify CTA width
      const newWidth = prompt('Modify proposed Pay button width (px):', '280');
      if (newWidth && !isNaN(Number(newWidth))) {
        const modifiedOps = JSON.parse(JSON.stringify(proposal.operations));
        modifiedOps[0].proposedValue.w = Number(newWidth);
        this.callbacks.onModify(modifiedOps);
      }
    });
  }
}
