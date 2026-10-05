export class RuntimeView {
  private container: HTMLElement;
  private refreshInterval: any;

  constructor(containerId: string) {
    const el = document.getElementById(containerId);
    if (!el) throw new Error(`Container ${containerId} not found`);
    this.container = el;
    this.render();
  }

  public async render() {
    if (!window.jarvisAPI?.getRuntimeState) return;

    try {
      const stateRes: any = await window.jarvisAPI.getRuntimeState();
      const eventsRes: any = await window.jarvisAPI.getRuntimeEvents();
      
      const rtState = stateRes?.runtime_state || {};
      const events = eventsRes?.events || [];

      this.container.innerHTML = `
        <div style="background: rgba(15, 23, 42, 0.95); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 12px; padding: 20px; color: #f8fafc; font-family: 'Inter', sans-serif;">
          
          <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; margin-bottom: 14px;">
            <h3 style="margin: 0; display: flex; align-items: center; gap: 8px;">
              <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: ${rtState.status === 'RUNNING' ? '#10b981' : rtState.status === 'RECOVERING' ? '#f59e0b' : '#ef4444'};"></span>
              Runtime Diagnostics
            </h3>
            <div style="display: flex; gap: 12px; font-size: 0.8rem;">
              <span>Status: <strong style="color: #38bdf8;">${rtState.status || 'UNKNOWN'}</strong></span>
              <span>Python: <strong style="color: #10b981;">CONNECTED</strong></span>
            </div>
          </div>

          <!-- Recovery UI -->
          ${rtState.recovery_required ? `
            <div style="background: rgba(220, 38, 38, 0.15); border: 1px solid #ef4444; border-radius: 8px; padding: 14px; margin-bottom: 16px;">
              <h4 style="margin: 0 0 8px 0; color: #fca5a5;">⚠ JARVIS RECOVERY REQUIRED</h4>
              <p style="margin: 0 0 12px 0; color: #fecaca; font-size: 0.85rem;">
                JARVIS was interrupted. Recovery State: <strong>${rtState.recovery_state}</strong><br/>
                No automatic replay is allowed. The current context will be inspected before any further action.
              </p>
              <div style="display: flex; gap: 10px;">
                <button id="rt-btn-reconcile" style="background: #3b82f6; color: white; border: none; padding: 6px 14px; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 0.8rem;">Reconcile & Resume</button>
                <button id="rt-btn-discard" style="background: #1e293b; color: #f8fafc; border: 1px solid #334155; padding: 6px 14px; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 0.8rem;">Discard Task</button>
              </div>
            </div>
          ` : ''}

          <!-- Event Inspector -->
          <h4 style="margin: 0 0 10px 0; font-size: 0.85rem; color: #94a3b8;">Event Timeline (Latest ${events.length})</h4>
          <div style="max-height: 200px; overflow-y: auto; background: rgba(0,0,0,0.3); border: 1px solid #334155; border-radius: 8px; padding: 10px;">
            <table style="width: 100%; border-collapse: collapse; font-size: 0.75rem;">
              <tr style="text-align: left; color: #64748b; border-bottom: 1px solid #334155;">
                <th style="padding: 4px;">Seq</th>
                <th style="padding: 4px;">Type</th>
                <th style="padding: 4px;">Task ID</th>
                <th style="padding: 4px;">Timestamp</th>
              </tr>
              ${events.slice().reverse().map((evt: any) => `
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                  <td style="padding: 4px; color: #cbd5e1;">${evt.sequence}</td>
                  <td style="padding: 4px; color: #38bdf8;">${evt.event_type}</td>
                  <td style="padding: 4px; color: #cbd5e1;">${evt.task_id || '-'}</td>
                  <td style="padding: 4px; color: #64748b;">${new Date(evt.timestamp).toLocaleTimeString()}</td>
                </tr>
              `).join('')}
            </table>
          </div>
          
        </div>
      `;

      this.attachListeners();
    } catch (e) {
      console.error("Failed to render runtime view:", e);
    }
  }

  private attachListeners() {
    document.getElementById('rt-btn-reconcile')?.addEventListener('click', async () => {
      if (window.jarvisAPI?.recoverRuntime) {
        await window.jarvisAPI.recoverRuntime('reconcile', 'vscode');
        this.render();
      }
    });

    document.getElementById('rt-btn-discard')?.addEventListener('click', async () => {
      if (window.jarvisAPI?.recoverRuntime) {
        await window.jarvisAPI.recoverRuntime('discard');
        this.render();
      }
    });
  }

  public startPolling(ms: number = 2000) {
    this.refreshInterval = setInterval(() => this.render(), ms);
  }

  public stopPolling() {
    if (this.refreshInterval) clearInterval(this.refreshInterval);
  }
}
