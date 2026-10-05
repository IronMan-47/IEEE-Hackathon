
function escapeHtml(unsafe: any): string {
  return String(unsafe)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
export interface PerceptionViewCallbacks {
  onPerceiveNow: (requestCapture: boolean) => Promise<void>;
  onTogglePolicy: (enabled: boolean) => Promise<void>;
}

export class PerceptionView {
  private isInspectorOpen: boolean = false;

  constructor(
    private container: HTMLElement,
    private callbacks: PerceptionViewCallbacks
  ) {}

  public render(perception: any): void {
    if (!perception) {
      this.container.innerHTML = `
        <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 12px; margin-top: 10px; font-family: sans-serif; color: #94A3B8; font-size: 11px;">
          👁️ Perception offline or not initialized.
        </div>
      `;
      return;
    }

    const app = perception.active_application || { name: 'Unknown', process_name: 'unknown.exe' };
    const win = perception.active_window || { title: 'Unknown', width: 0, height: 0 };
    const screen = perception.screen_metadata || { primary_width: 1920, primary_height: 1080 };
    const cap = perception.capture_metadata || { captured: false };
    const isEnabled = perception.perception_enabled !== false;
    const isExcluded = perception.is_excluded === true;
    const classification = perception.classification || 'UNKNOWN';
    const appContext = perception.application_context || {
      application: 'unknown',
      status: 'UNSUPPORTED',
      confidence: 'UNAVAILABLE',
      privacy: 'PUBLIC',
      data: {}
    };

    const classColors: Record<string, { bg: string; fg: string }> = {
      CODE_EDITOR: { bg: 'rgba(59, 130, 246, 0.2)', fg: '#60A5FA' },
      BROWSER: { bg: 'rgba(16, 185, 129, 0.2)', fg: '#34D399' },
      DESIGN_TOOL: { bg: 'rgba(236, 72, 153, 0.2)', fg: '#F472B6' },
      TERMINAL: { bg: 'rgba(245, 158, 11, 0.2)', fg: '#FBBF24' },
      DOCUMENT_EDITOR: { bg: 'rgba(168, 85, 247, 0.2)', fg: '#C084FC' },
      UNKNOWN: { bg: 'rgba(100, 116, 139, 0.2)', fg: '#94A3B8' }
    };
    const cStyle = classColors[classification] || classColors['UNKNOWN'];

    const statusBg = appContext.status === 'AVAILABLE' ? 'rgba(16, 185, 129, 0.2)' : appContext.status === 'PARTIAL' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(148, 163, 184, 0.2)';
    const statusFg = appContext.status === 'AVAILABLE' ? '#34D399' : appContext.status === 'PARTIAL' ? '#FBBF24' : '#94A3B8';

    this.container.innerHTML = `
      <div class="perception-panel" style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 12px; margin-top: 10px; font-family: sans-serif; color: #E2E8F0;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 8px; margin-bottom: 10px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-weight: 700; color: #10B981; font-size: 13px;">👁️ DESKTOP PERCEPTION</span>
            <span style="background: ${cStyle.bg}; color: ${cStyle.fg}; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700;">
              ${classification}
            </span>
            ${isExcluded ? '<span style="background: rgba(239, 68, 68, 0.2); color: #FCA5A5; padding: 2px 6px; border-radius: 4px; font-size: 10px;">EXCLUDED</span>' : ''}
          </div>
          <div style="display: flex; gap: 6px;">
            <button id="btn-toggle-policy" style="background: ${isEnabled ? '#334155' : '#DC2626'}; color: white; border: none; border-radius: 4px; padding: 3px 8px; font-size: 11px; cursor: pointer;">
              ${isEnabled ? 'Disable Perception' : 'Enable Perception'}
            </button>
            <button id="btn-perceive-now" style="background: #10B981; color: white; border: none; border-radius: 4px; padding: 3px 8px; font-size: 11px; cursor: pointer; font-weight: 600;">
              🔍 Perceive Now
            </button>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 11px; margin-bottom: 10px;">
          <div>
            <div style="color: #64748B; font-size: 10px; text-transform: uppercase;">Active Application</div>
            <div style="font-weight: 700; color: #F8FAFC;">${app.name}</div>
            <div style="color: #94A3B8; font-family: monospace; font-size: 10px;">Process: ${app.process_name} (PID: ${app.pid || 'N/A'})</div>
          </div>
          <div>
            <div style="color: #64748B; font-size: 10px; text-transform: uppercase;">Window & Screen Geometry</div>
            <div style="color: #CBD5E1; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;" title="${win.title}">${win.title}</div>
            <div style="color: #94A3B8; font-family: monospace; font-size: 10px;">
              Win: ${win.width}×${win.height} (${win.x},${win.y}) | Screen: ${screen.primary_width}×${screen.primary_height}
            </div>
          </div>
        </div>

        <!-- Application Context Section -->
        <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 6px; padding: 8px;">
          <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed rgba(255, 255, 255, 0.1); padding-bottom: 6px; margin-bottom: 6px;">
            <div style="display: flex; align-items: center; gap: 6px;">
              <span style="font-weight: 700; color: #38BDF8; font-size: 11px;">🧠 APPLICATION CONTEXT</span>
              <span style="background: ${statusBg}; color: ${statusFg}; padding: 1px 6px; border-radius: 3px; font-size: 9px; font-weight: 700;">
                ${appContext.status}
              </span>
              <span style="color: #64748B; font-size: 10px;">Adapter: ${appContext.application}</span>
            </div>
            <button id="btn-toggle-inspector" style="background: #334155; color: #94A3B8; border: none; border-radius: 3px; padding: 2px 6px; font-size: 10px; cursor: pointer;">
              ${this.isInspectorOpen ? 'Hide JSON Inspector' : 'Show JSON Inspector'}
            </button>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 11px;">
            <div>
              <span style="color: #64748B; font-size: 10px;">Primary Context: </span>
              <span style="color: #F8FAFC; font-weight: 600;">
                ${appContext.data.workspace?.name || appContext.data.file || appContext.data.page_title || appContext.data.shell || 'N/A'}
              </span>
            </div>
            <div>
              <span style="color: #64748B; font-size: 10px;">Active Target: </span>
              <span style="color: #F8FAFC; font-weight: 600;">
                ${appContext.data.active_file?.name || appContext.data.browser || appContext.data.window_title || 'N/A'}
              </span>
            </div>
          </div>

          ${this.isInspectorOpen ? `
            <div style="margin-top: 8px; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 6px;">
              <div style="color: #64748B; font-size: 10px; margin-bottom: 4px;">Sanitized Context Payload (Passed to Agent):</div>
              <pre style="background: #0F172A; border: 1px solid #334155; color: #38BDF8; font-family: monospace; font-size: 10px; padding: 6px; border-radius: 4px; max-height: 120px; overflow-y: auto; margin: 0;">${escapeHtml(JSON.stringify(appContext, null, 2))}</pre>
            </div>
          ` : ''}
        </div>

        ${cap.captured && cap.data_base64 ? `
          <div style="margin-top: 10px; border-top: 1px dashed rgba(255, 255, 255, 0.1); padding-top: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
              <span style="font-size: 10px; color: #34D399; font-weight: 600;">📸 Window Capture Preview (${cap.capture_type})</span>
              <button id="btn-discard-screenshot" style="background: #334155; color: #94A3B8; border: none; border-radius: 3px; padding: 2px 6px; font-size: 10px; cursor: pointer;">Discard Preview</button>
            </div>
            <div style="text-align: center; background: #000; border-radius: 4px; padding: 4px; max-height: 120px; overflow: hidden;">
              <img src="data:image/png;base64,${cap.data_base64}" style="max-width: 100%; max-height: 110px; border-radius: 2px;" alt="Captured window" />
            </div>
          </div>
        ` : ''}
      </div>
    `;

    this.bindEvents(isEnabled);
  }

  private bindEvents(currentEnabled: boolean): void {
    const btnPerceive = this.container.querySelector('#btn-perceive-now');
    if (btnPerceive) {
      btnPerceive.addEventListener('click', async () => {
        await this.callbacks.onPerceiveNow(true);
      });
    }

    const btnToggle = this.container.querySelector('#btn-toggle-policy');
    if (btnToggle) {
      btnToggle.addEventListener('click', async () => {
        await this.callbacks.onTogglePolicy(!currentEnabled);
      });
    }

    const btnInspector = this.container.querySelector('#btn-toggle-inspector');
    if (btnInspector) {
      btnInspector.addEventListener('click', () => {
        this.isInspectorOpen = !this.isInspectorOpen;
        btnInspector.textContent = this.isInspectorOpen ? 'Hide JSON Inspector' : 'Show JSON Inspector';
        const inspectorDiv = this.container.querySelector('pre');
        if (inspectorDiv && inspectorDiv.parentElement) {
          inspectorDiv.parentElement.style.display = this.isInspectorOpen ? 'block' : 'none';
        }
      });
    }

    const btnDiscard = this.container.querySelector('#btn-discard-screenshot');
    if (btnDiscard) {
      btnDiscard.addEventListener('click', async () => {
        await this.callbacks.onPerceiveNow(false);
      });
    }
  }
}
