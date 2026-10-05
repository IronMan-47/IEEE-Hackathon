import sys

content = """import { OverlayState } from '../app.js'; // Assuming this gets bundled correctly, but let's just make it standalone

export type OverlayState = {
  runtimeState: string;
  isExpanded: boolean;
  activeApp: string;
  activeFile?: string;
  isMicActive: boolean;
  isScreenActive: boolean;
  activeTask?: any;
  currentProposal?: any;
  recoveryState?: any;
};

export class OverlayView {
  public container: HTMLElement;
  public state: OverlayState = {
    runtimeState: 'IDLE',
    isExpanded: false,
    activeApp: 'Unknown',
    isMicActive: false,
    isScreenActive: false
  };

  private hasInitialized = false;

  constructor(
    containerId: string,
    private callbacks: {
      onToggleExpand: () => void;
      onSubmitCommand: (text: string) => void;
      onEmergencyStop: () => void;
      onApproveProposal: () => void;
      onRejectProposal: () => void;
      onToggleMic: () => void;
    }
  ) {
    const el = document.getElementById(containerId);
    if (!el) throw new Error(`Container ${containerId} not found`);
    this.container = el;
    this.render();
  }

  public updateState(newState: Partial<OverlayState>) {
    this.state = { ...this.state, ...newState };
    this.render();
  }

  private render() {
    if (!this.hasInitialized) {
      this.initialRender();
      this.hasInitialized = true;
    }
    this.updateDOM();
  }

  private initialRender() {
    this.container.innerHTML = `
      <div class="overlay-header">
        <div class="overlay-brand">
          <div id="status-dot" class="status-dot"></div>
          JARVIS <span id="status-text" style="color:var(--text-secondary); font-weight:400; font-size:0.85rem; margin-left:8px;"></span>
        </div>
        <div class="overlay-controls">
          <button id="btn-toggle-expand" class="icon-btn" title="Toggle Size">?</button>
          <button id="btn-emergency" class="btn-emergency" title="Emergency Stop">STOP</button>
        </div>
      </div>

      <div class="privacy-bar" id="privacy-bar-container"></div>

      <div class="overlay-content">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <p class="text-xs">CURRENT APP</p>
            <p id="app-name-text" class="text-sm font-bold"></p>
            <p id="app-file-text" class="text-xs text-mono" style="display:none;"></p>
          </div>
          <div id="review-btn-container"></div>
        </div>

        <div id="expanded-content" class="overlay-expanded-content"></div>

        <div class="command-input-container">
          <input type="text" id="cmd-input" class="command-input" placeholder="Ask JARVIS (Ctrl+Shift+Space)..." />
          <button id="btn-mic" class="icon-btn">??</button>
        </div>
      </div>
    `;

    document.getElementById('btn-toggle-expand')?.addEventListener('click', () => this.callbacks.onToggleExpand());
    document.getElementById('btn-emergency')?.addEventListener('click', () => this.callbacks.onEmergencyStop());
    document.getElementById('btn-mic')?.addEventListener('click', () => this.callbacks.onToggleMic());

    const cmdInput = document.getElementById('cmd-input') as HTMLInputElement;
    cmdInput?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (cmdInput.value.trim()) {
          this.callbacks.onSubmitCommand(cmdInput.value.trim());
          cmdInput.value = '';
        }
      }
    });

    const api = (window as any).jarvisAPI;
    if (api && api.requestIgnoreMouseEvents) {
      this.container.addEventListener('mouseenter', () => api.requestIgnoreMouseEvents(false));
      this.container.addEventListener('mouseleave', () => api.requestIgnoreMouseEvents(true));
      api.requestIgnoreMouseEvents(true);
    }
  }

  private updateDOM() {
    this.container.className = this.state.isExpanded ? 'jarvis-overlay-compact jarvis-overlay-expanded' : 'jarvis-overlay-compact';
    
    let statusClass = 'idle';
    if (this.state.runtimeState === 'EXECUTING') statusClass = ''; 
    if (this.state.runtimeState === 'BLOCKED' || this.state.runtimeState === 'WAITING_FOR_HUMAN') statusClass = 'blocked';
    if (this.state.runtimeState === 'ERROR' || this.state.runtimeState === 'SAFE_STOPPED') statusClass = 'error';

    const dot = document.getElementById('status-dot');
    if (dot) dot.className = \`status-dot \${statusClass}\`;

    const txt = document.getElementById('status-text');
    if (txt) txt.textContent = this.state.runtimeState.replace(/_/g, ' ');

    const expandBtn = document.getElementById('btn-toggle-expand');
    if (expandBtn) expandBtn.textContent = this.state.isExpanded ? '?' : '?';

    const privacy = document.getElementById('privacy-bar-container');
    if (privacy) {
      privacy.innerHTML = \`
        <span class="privacy-item \${this.state.isMicActive ? 'active' : 'inactive'}">
          \${this.state.isMicActive ? '?? MIC: LISTENING' : '?? MIC: OFF'}
        </span>
        <span class="privacy-item \${this.state.isScreenActive ? 'active' : 'inactive'}">
          \${this.state.isScreenActive ? '?? SCREEN: ACTIVE' : '?? SCREEN: OFF'}
        </span>
      \`;
    }

    const appName = document.getElementById('app-name-text');
    if (appName) appName.textContent = this.state.activeApp || 'Unknown';

    const appFile = document.getElementById('app-file-text');
    if (appFile) {
      if (this.state.activeFile) {
        appFile.style.display = 'block';
        appFile.textContent = this.state.activeFile;
      } else {
        appFile.style.display = 'none';
      }
    }

    const hasProposal = !!this.state.currentProposal;
    const reviewContainer = document.getElementById('review-btn-container');
    if (reviewContainer) {
      if (this.state.runtimeState === 'WAITING_FOR_HUMAN' && hasProposal) {
        reviewContainer.innerHTML = \`<button id="btn-review" class="btn-primary" style="width:auto; padding: 4px 12px; font-size:0.75rem;">Review Proposal ?</button>\`;
        document.getElementById('btn-review')?.addEventListener('click', () => {
          if (!this.state.isExpanded) this.callbacks.onToggleExpand();
        });
      } else {
        reviewContainer.innerHTML = '';
      }
    }

    const micBtn = document.getElementById('btn-mic');
    if (micBtn) {
      micBtn.style.background = this.state.isMicActive ? '#ef4444' : 'rgba(255,255,255,0.1)';
    }

    const expanded = document.getElementById('expanded-content');
    if (expanded) {
      expanded.innerHTML = this.renderExpandedContent();
      document.getElementById('btn-approve')?.addEventListener('click', () => this.callbacks.onApproveProposal());
      document.getElementById('btn-reject')?.addEventListener('click', () => this.callbacks.onRejectProposal());
    }
  }

  private renderExpandedContent(): string {
    let html = '<hr style="border:0; border-top:1px solid rgba(255,255,255,0.1); margin:16px 0;" />';

    if (this.state.recoveryState) {
      return html + \`
        <div class="overlay-section" style="border-color: var(--danger)">
          <h3 class="overlay-section-title" style="color:var(--danger)">RECOVERY REQUIRED</h3>
          <p class="text-sm">JARVIS was interrupted. Execution state is uncertain.</p>
          <div style="margin-top:12px; display:flex; gap:8px;">
            <button class="btn-secondary">Reinspect</button>
            <button class="btn-secondary">Cancel Task</button>
          </div>
        </div>
      \`;
    }

    if (this.state.activeTask) {
      html += \`
        <div class="overlay-section">
          <h3 class="overlay-section-title">CURRENT TASK</h3>
          <p class="text-sm" style="margin-bottom:12px;">\${this.state.activeTask.user_request}</p>
          
          <div class="timeline">
            \${this.state.activeTask.steps.map((step: any, i: number) => {
              const isCurrent = i === this.state.activeTask.current_step_index;
              const isDone = step.status === 'COMPLETED';
              let icon = isDone ? '?' : (isCurrent ? '?' : '?');
              let color = isDone ? 'var(--success)' : (isCurrent ? 'var(--accent)' : 'var(--text-secondary)');
              return \`
                <div class="timeline-item" style="color:\${color}">
                  <p class="text-sm" style="font-weight:\${isCurrent ? '600' : '400'}">\${icon} [\${step.target_domain || 'system'}] \${step.title}</p>
                  \${step.cross_app_handoff ? \`<p class="text-xs" style="color:var(--warning)">? Handoff to \${step.cross_app_handoff.target_application}</p>\` : ''}
                </div>
              \`;
            }).join('')}
          </div>
        </div>
      \`;
    }

    if (this.state.currentProposal && this.state.runtimeState === 'WAITING_FOR_HUMAN') {
      const p = this.state.currentProposal;
      html += \`
        <div class="overlay-section" style="border-color: var(--accent);">
          <h3 class="overlay-section-title">PROPOSED CHANGE</h3>
          <p class="text-sm"><strong>Domain:</strong> \${p.domain}</p>
          <p class="text-sm"><strong>Action:</strong> \${p.action_type}</p>
          <p class="text-sm"><strong>Target:</strong> \${p.target}</p>
          <p class="text-sm" style="margin-top:8px; color:var(--text-secondary)"><strong>Why:</strong> JARVIS generated this bounded change based on the active evidence.</p>
          <p class="text-xs" style="margin-top:4px;">Risk: <span style="color:var(--success)">\${p.risk_level}</span></p>
          
          <div style="display:flex; gap:8px; margin-top:12px;">
            <button id="btn-approve" class="btn-primary">Approve & Execute</button>
            <button id="btn-reject" class="btn-secondary">Reject</button>
          </div>
        </div>
      \`;
    } else if (!this.state.activeTask) {
      html += \`
        <div style="text-align:center; padding: 20px 0;">
          <p class="text-sm" style="color:var(--text-secondary)">No active task.</p>
          <p class="text-xs" style="margin-top:8px;">Ready for your next request.</p>
        </div>
      \`;
    }

    return html;
  }
}
"""

with open('src/apps/desktop/renderer/components/overlay-view.ts', 'w', encoding='utf-8') as f:
    f.write(content)
