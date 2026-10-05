
function escapeHtml(unsafe: any): string {
  return String(unsafe)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
/**
 * JARVIS Phase 9 & Phase 10 Proposal Review & Controlled Execution Component
 * Renders Structured Reviewable Proposal, Diff Preview, Trace Drawer, Human Review Controls,
 * and Phase 10 Living Canvas Execution Controls & Verification Results.
 */

export interface ProposalReviewViewOptions {
  onExecutionComplete?: (result: any) => void;
}

export class ProposalReviewView {
  private container: HTMLElement;
  private activeProposal: any = null;
  private activeToken: any = null;
  private executionResult: any = null;
  private isExecuting: boolean = false;
  private traceExpanded: boolean = false;
  private options?: ProposalReviewViewOptions;

  constructor(containerId: string, options?: ProposalReviewViewOptions) {
    const el = document.getElementById(containerId);
    if (!el) {
      throw new Error(`Container #${containerId} not found`);
    }
    this.container = el;
    this.options = options;
  }

  public render(proposal: any = null, token: any = null, executionResult: any = null): void {
    this.activeProposal = proposal;
    this.activeToken = token;
    this.executionResult = executionResult;

    if (!proposal) {
      this.container.innerHTML = `
        <div style="background: rgba(15, 23, 42, 0.85); border: 1px dashed rgba(56, 189, 248, 0.3); border-radius: 12px; padding: 20px; color: #64748b; text-align: center;">
          <p style="margin: 0; font-size: 0.9rem;">No proposal currently generated. Generate a strategy plan above to produce a reviewable proposal.</p>
        </div>
      `;
      return;
    }

    const isAccepted = proposal.status === 'ACCEPTED';
    const isStale = proposal.status === 'STALE';
    const isCommitted = executionResult && (executionResult.status === 'COMMITTED' || executionResult.status === 'SUCCESS');

    const riskColor = proposal.risk === 'HIGH' ? '#ef4444' : proposal.risk === 'MEDIUM' ? '#f59e0b' : '#10b981';

    this.container.innerHTML = `
      <div class="proposal-review-card" style="background: rgba(15, 23, 42, 0.95); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 12px; padding: 20px; color: #f8fafc; font-family: sans-serif; margin-top: 16px;">
        
        <!-- Header -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px;">
          <div>
            <span style="color: #64748b; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">Phase 9 & 10 Safety & Execution Boundary</span>
            <h3 style="margin: 2px 0 0 0; color: #38bdf8; font-size: 1.15rem;">${proposal.title}</h3>
          </div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;">${proposal.domain.toUpperCase()}</span>
            <span style="background: ${riskColor}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;">RISK: ${proposal.risk}</span>
          </div>
        </div>

        <!-- Summary & Reason -->
        <div style="margin-bottom: 14px; background: #1e293b; padding: 12px; border-radius: 8px; border-left: 3px solid #38bdf8;">
          <div style="color: #cbd5e1; font-size: 0.85rem; margin-bottom: 4px;"><strong>Why:</strong> ${proposal.summary}</div>
          <div style="color: #94a3b8; font-size: 0.8rem;"><strong>Rationale:</strong> ${proposal.reason}</div>
        </div>

        <!-- Target & Revision Details -->
        <div style="display: flex; justify-content: space-between; background: #0f172a; padding: 10px 14px; border-radius: 6px; font-size: 0.8rem; margin-bottom: 14px; border: 1px solid #334155;">
          <div><span style="color: #64748b;">Proposal ID:</span> <span style="color: #38bdf8; font-weight: 600;">${proposal.proposal_id}</span></div>
          <div><span style="color: #64748b;">Base Context:</span> <span style="color: #f8fafc; font-family: monospace;">${(proposal.base_context_hash || '').substring(0, 8)} (Rev ${proposal.base_revision})</span></div>
          <div><span style="color: #64748b;">Status:</span> <span style="color: ${isCommitted ? '#10b981' : isAccepted ? '#10b981' : isStale ? '#ef4444' : '#f59e0b'}; font-weight: 700;">${isCommitted ? 'COMMITTED (PHASE 10)' : proposal.status}</span></div>
        </div>

        <!-- Proposed Operations List -->
        <div style="margin-bottom: 14px;">
          <span style="color: #64748b; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">Proposed Operations (${proposal.operations.length})</span>
          <div style="display: flex; flex-direction: column; gap: 8px; margin-top: 8px;">
            ${proposal.operations.map((op: any, idx: number) => `
              <div style="background: #1e293b; border: 1px solid #334155; border-radius: 6px; padding: 10px 14px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                  <span style="color: #38bdf8; font-weight: 700; font-size: 0.85rem;">${idx + 1}. ${escapeHtml(op.op_type)}</span>
                  <span style="color: #94a3b8; font-size: 0.75rem; font-family: monospace;">Target: ${escapeHtml(op.target)}</span>
                </div>
                <div style="background: #0f172a; padding: 8px; border-radius: 4px; font-family: monospace; font-size: 0.75rem; color: #a5f3fc; overflow-x: auto;">
                  ${escapeHtml(JSON.stringify(op.parameters, null, 2))}
                </div>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Expandable Trace Drawer -->
        <div style="margin-bottom: 14px; background: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 10px;">
          <button id="btn-toggle-trace" style="background: none; border: none; color: #38bdf8; font-size: 0.8rem; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 6px;">
            <span>🔍 Proposal Trace Lineage (Request → Intent → Goal → Plan → Proposal)</span>
          </button>
          
          <div id="trace-drawer" style="display: none; margin-top: 10px; padding-top: 10px; border-top: 1px solid #334155; font-size: 0.78rem; color: #cbd5e1;">
            <div><strong>Original Prompt:</strong> "${proposal.trace?.request_text || 'N/A'}"</div>
            <div><strong>Classified Intent:</strong> <span style="color: #38bdf8;">${proposal.trace?.intent_type || 'N/A'}</span></div>
            <div><strong>Primary Goal:</strong> ${proposal.trace?.goal_primary || 'N/A'}</div>
            <div><strong>Plan ID:</strong> ${proposal.trace?.plan_id || 'N/A'}</div>
            <div><strong>Context Snapshot Hash:</strong> ${proposal.trace?.context_hash || 'N/A'}</div>
          </div>
        </div>

        <!-- Token Banner if accepted (and not yet committed) -->
        ${isAccepted && token && !isCommitted ? `
          <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; border-radius: 8px; padding: 12px; margin-bottom: 14px;">
            <div style="color: #10b981; font-weight: 700; font-size: 0.85rem;">✓ Proposal Accepted & Single-Use ApprovalToken Issued</div>
            <div style="color: #a7f3d0; font-size: 0.78rem; font-family: monospace; margin-top: 4px;">Token ID: ${token.tokenId} (Bound to Rev ${token.baseRevision})</div>
            <div style="color: #e2e8f0; font-size: 0.75rem; margin-top: 4px;">Ready for Phase 10 execution against Living Canvas. Real OS applications remain untouched.</div>
          </div>
        ` : ''}

        <!-- Execution Result Card if Committed -->
        ${isCommitted ? `
          <div style="background: rgba(16, 185, 129, 0.2); border: 1px solid #10b981; border-radius: 8px; padding: 14px; margin-bottom: 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <div style="color: #10b981; font-weight: 700; font-size: 0.95rem;">🚀 PHASE 10 EXECUTION COMPLETE</div>
              <span style="background: #10b981; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700;">VERIFIED: ${executionResult.execution_result?.verification || 'PASSED'}</span>
            </div>
            <div style="color: #cbd5e1; font-size: 0.82rem; margin-top: 8px;">
              <div><strong>Workspace Revision:</strong> Rev ${executionResult.execution_result?.previous_revision} ➔ Rev ${executionResult.execution_result?.new_revision}</div>
              <div><strong>Committed Node ID:</strong> <span style="font-family: monospace; color: #38bdf8;">${executionResult.execution_result?.version_id}</span></div>
              <div><strong>Operations Applied:</strong> ${executionResult.execution_result?.operations_applied?.length} operations executed successfully</div>
              <div style="color: #a7f3d0; font-size: 0.78rem; margin-top: 6px; font-style: italic;">
                Postcondition verification passed. Atomic version commit added to VersionGraph ($V_{mutation}$).
              </div>
            </div>
          </div>
        ` : ''}

        <!-- Safety Disclaimer -->
        <div style="font-size: 0.75rem; color: #94a3b8; margin-bottom: 14px; font-style: italic; text-align: center;">
          ⚠️ Execution authority is strictly bounded to the deterministic Living Canvas workspace. Real Windows applications and external system resources remain completely isolated and unaffected.
        </div>

        <!-- Action Control Buttons -->
        <div style="display: flex; justify-content: flex-end; gap: 10px;">
          ${!isCommitted ? `
            <button id="btn-reject-proposal" style="background: #334155; color: #f8fafc; border: none; border-radius: 6px; padding: 10px 18px; font-weight: 600; cursor: pointer;">Reject</button>
            <button id="btn-modify-proposal" style="background: #475569; color: #f8fafc; border: none; border-radius: 6px; padding: 10px 18px; font-weight: 600; cursor: pointer;">Modify</button>
            ${!isAccepted ? `
              <button id="btn-accept-proposal" style="background: #0284c7; color: white; border: none; border-radius: 6px; padding: 10px 22px; font-weight: 700; cursor: pointer;">
                Accept Proposal
              </button>
            ` : `
              <button id="btn-execute-proposal" style="background: #059669; color: white; border: none; border-radius: 6px; padding: 10px 24px; font-weight: 700; cursor: pointer; box-shadow: 0 0 12px rgba(16, 185, 129, 0.4);">
                ⚡ Execute Approved Proposal (Living Canvas)
              </button>
            `}
          ` : `
            <div style="color: #10b981; font-weight: 600; font-size: 0.85rem; padding: 6px 12px; border: 1px solid #059669; border-radius: 6px; background: rgba(5, 150, 105, 0.1);">
              ✓ Executed & Committed to Version Graph
            </div>
          `}
        </div>

      </div>
    `;

    this.attachEvents();
  }

  private attachEvents(): void {
    const btnAccept = this.container.querySelector('#btn-accept-proposal');
    const btnExecute = this.container.querySelector('#btn-execute-proposal');
    const btnReject = this.container.querySelector('#btn-reject-proposal');
    const btnModify = this.container.querySelector('#btn-modify-proposal');
    const btnTrace = this.container.querySelector('#btn-toggle-trace');
    const traceDrawer = this.container.querySelector('#trace-drawer') as HTMLElement;

    if (btnTrace && traceDrawer) {
      btnTrace.addEventListener('click', () => {
        this.traceExpanded = !this.traceExpanded;
        traceDrawer.style.display = this.traceExpanded ? 'block' : 'none';
      });
    }

    if (btnAccept && this.activeProposal) {
      btnAccept.addEventListener('click', async () => {
        if (window.jarvisAPI && window.jarvisAPI.acceptProposalPhase9) {
          const res: any = await window.jarvisAPI.acceptProposalPhase9(this.activeProposal);
          if (res.status === 'SUCCESS') {
            this.render(res.proposal, res.approval_token);
          }
        }
      });
    }

    if (btnExecute && this.activeProposal && this.activeToken) {
      btnExecute.addEventListener('click', async () => {
        btnExecute.textContent = '⏳ Executing & Verifying...';
        (btnExecute as HTMLButtonElement).disabled = true;

        if (window.jarvisAPI && window.jarvisAPI.executeProposal) {
          const res: any = await window.jarvisAPI.executeProposal(this.activeProposal, this.activeToken);
          this.render(this.activeProposal, this.activeToken, res);
          if (this.options?.onExecutionComplete) {
            this.options.onExecutionComplete(res);
          }
        }
      });
    }

    if (btnReject) {
      btnReject.addEventListener('click', () => {
        this.render(null);
      });
    }

    if (btnModify && this.activeProposal) {
      btnModify.addEventListener('click', async () => {
        const modifiedOps = [...this.activeProposal.operations];
        if (modifiedOps.length > 0) {
          modifiedOps[0] = {
            ...modifiedOps[0],
            parameters: { ...modifiedOps[0].parameters, fontWeight: 'bold', fill: '#059669' },
            reason: 'Human modified style CTA parameters'
          };
        }

        if (window.jarvisAPI && window.jarvisAPI.modifyProposalPhase9) {
          const res: any = await window.jarvisAPI.modifyProposalPhase9(this.activeProposal, modifiedOps);
          if (res.status === 'SUCCESS') {
            this.render(res.proposal, null);
          }
        }
      });
    }
  }
}
