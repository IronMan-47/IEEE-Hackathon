/**
 * JARVIS Phase 13 — Visual Understanding Inspector Component
 * Renders structured visual context summaries, detected regions, visual taxonomy elements,
 * confidence badges, provenance tags, Privacy controls, and Living Canvas Ground-Truth evaluations.
 * Read-only inspection overlay strictly non-executable.
 */

export class VisualView {
  private container: HTMLElement;
  private currentContext: any = null;
  private currentEval: any = null;
  private selectedElement: any = null;

  constructor(containerId: string) {
    const el = document.getElementById(containerId);
    if (!el) {
      throw new Error(`Container #${containerId} not found`);
    }
    this.container = el;
  }

  public render(vctx: any = null, evalResult: any = null): void {
    this.currentContext = vctx;
    this.currentEval = evalResult;

    if (!vctx) {
      this.container.innerHTML = `
        <div class="card visual-card">
          <div class="card-header">
            <h3>👁️ Multimodal Visual Perception Inspector</h3>
            <span class="badge badge-info">Phase 13</span>
          </div>
          <div class="card-body">
            <p class="text-muted">No visual perception context active.</p>
            <div class="action-row" style="margin-top: 10px;">
              <button id="btn-visual-analyze-vscode" class="btn btn-secondary btn-sm">Analyze VS Code</button>
              <button id="btn-visual-analyze-browser" class="btn btn-secondary btn-sm">Analyze Browser</button>
              <button id="btn-visual-analyze-canvas" class="btn btn-primary btn-sm">Analyze Living Canvas</button>
              <button id="btn-visual-analyze-login" class="btn btn-warning btn-sm">Analyze Login Screen</button>
            </div>
          </div>
        </div>
      `;
      this.attachEvents();
      return;
    }

    const confLevel = vctx.confidence_level || 'HIGH_CONFIDENCE';
    const confBadgeClass = confLevel === 'HIGH_CONFIDENCE' ? 'badge-success' : (confLevel === 'MEDIUM_CONFIDENCE' ? 'badge-warning' : 'badge-danger');
    const sensitiveBadge = vctx.is_sensitive ? `<span class="badge badge-danger">🔒 Redacted (${vctx.redacted_elements_count})</span>` : '';

    const elementsList = (vctx.elements || []).map((e: any) => {
      const isSelected = this.selectedElement && this.selectedElement.id === e.id;
      return `
        <div class="visual-elem-item ${isSelected ? 'selected' : ''}" data-elem-id="${e.id}" style="padding: 6px 10px; border-bottom: 1px solid #333; cursor: pointer;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <strong style="font-size: 12px; color: #61dafb;">[${e.type}] ${e.id}</strong>
            <span class="badge badge-sm" style="font-size: 10px; background: #222;">${(e.confidence * 100).toFixed(0)}%</span>
          </div>
          <div style="font-size: 11px; color: #ccc; margin-top: 2px;">
            ${e.text ? `"${e.text.substring(0, 40)}${e.text.length > 40 ? '...' : ''}"` : '<em>No text</em>'}
          </div>
          <div style="font-size: 10px; color: #888;">
            Bounds: (${e.bounds.x}, ${e.bounds.y}, ${e.bounds.width}x${e.bounds.height}) | Src: ${e.provenance}
          </div>
        </div>
      `;
    }).join('');

    const evalSection = this.currentEval ? `
      <div class="eval-box" style="background: #1e2638; border: 1px solid #3b82f6; border-radius: 4px; padding: 10px; margin-top: 12px;">
        <h4 style="margin: 0 0 6px 0; font-size: 13px; color: #60a5fa;">🎯 Living Canvas Ground-Truth Evaluation</h4>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px;">
          <div>Ground Truth: <strong>${this.currentEval.ground_truth_count}</strong></div>
          <div>Visually Detected: <strong>${this.currentEval.visually_detected_count}</strong></div>
          <div>Precision: <strong style="color: #34d399;">${(this.currentEval.precision * 100).toFixed(1)}%</strong></div>
          <div>Recall: <strong style="color: #34d399;">${(this.currentEval.recall * 100).toFixed(1)}%</strong></div>
          <div>Mean IoU: <strong>${(this.currentEval.mean_iou * 100).toFixed(1)}%</strong></div>
          <div>Text Accuracy: <strong>${(this.currentEval.text_accuracy * 100).toFixed(1)}%</strong></div>
        </div>
      </div>
    ` : '';

    this.container.innerHTML = `
      <div class="card visual-card" style="border: 1px solid #4a5568;">
        <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
          <h3>👁️ Visual Perception Inspector</h3>
          <div>
            <span class="badge ${confBadgeClass}">${confLevel}</span>
            <span class="badge badge-info">${vctx.provenance}</span>
            ${sensitiveBadge}
          </div>
        </div>
        <div class="card-body">
          <div class="security-banner" style="background: #2d3748; padding: 6px 10px; border-radius: 4px; font-size: 11px; color: #a0aec0; margin-bottom: 10px;">
            ⚠️ <strong>Read-Only Inspection:</strong> Bounding box coordinates are non-executable visual metadata.
          </div>
          <div style="font-size: 12px; margin-bottom: 8px;">
            <strong>Application:</strong> ${vctx.application} (${vctx.application_class}) | <strong>Hash:</strong> <code>${vctx.context_hash.substring(0, 10)}...</code>
          </div>
          <div style="font-size: 12px; color: #e2e8f0; font-style: italic; background: #1a202c; padding: 8px; border-radius: 4px; margin-bottom: 10px;">
            "${vctx.visual_summary}"
          </div>

          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <strong style="font-size: 12px;">Detected Visual Elements (${(vctx.elements || []).length})</strong>
            <button id="btn-eval-ground-truth" class="btn btn-secondary btn-sm" style="font-size: 10px;">Evaluate Canvas Ground-Truth</button>
          </div>

          <div class="elements-scroll-container" style="max-height: 180px; overflow-y: auto; background: #141824; border: 1px solid #2d3748; border-radius: 4px;">
            ${elementsList || '<div style="padding: 10px; font-size: 11px; color: #718096;">No elements detected</div>'}
          </div>

          ${evalSection}

          <div class="action-row" style="margin-top: 10px; display: flex; gap: 6px; flex-wrap: wrap;">
            <button id="btn-visual-analyze-canvas" class="btn btn-primary btn-sm">Canvas</button>
            <button id="btn-visual-analyze-vscode" class="btn btn-secondary btn-sm">VS Code</button>
            <button id="btn-visual-analyze-browser" class="btn btn-secondary btn-sm">Browser</button>
            <button id="btn-visual-analyze-login" class="btn btn-warning btn-sm">Login</button>
            <button id="btn-visual-clear" class="btn btn-danger btn-sm">Clear</button>
          </div>
        </div>
      </div>
    `;

    this.attachEvents();
  }

  private attachEvents(): void {
    const btnVscode = this.container.querySelector('#btn-visual-analyze-vscode');
    if (btnVscode) {
      btnVscode.addEventListener('click', () => this.triggerAnalyze('VS_CODE_SCREEN'));
    }

    const btnBrowser = this.container.querySelector('#btn-visual-analyze-browser');
    if (btnBrowser) {
      btnBrowser.addEventListener('click', () => this.triggerAnalyze('BROWSER_SCREEN'));
    }

    const btnCanvas = this.container.querySelector('#btn-visual-analyze-canvas');
    if (btnCanvas) {
      btnCanvas.addEventListener('click', () => this.triggerAnalyze('LIVING_CANVAS_SCREEN'));
    }

    const btnLogin = this.container.querySelector('#btn-visual-analyze-login');
    if (btnLogin) {
      btnLogin.addEventListener('click', () => this.triggerAnalyze('LOGIN_SCREEN'));
    }

    const btnClear = this.container.querySelector('#btn-visual-clear');
    if (btnClear) {
      btnClear.addEventListener('click', async () => {
        if (window.jarvisAPI && window.jarvisAPI.clearVisualContext) {
          await window.jarvisAPI.clearVisualContext();
        }
        this.render(null);
      });
    }

    const btnEval = this.container.querySelector('#btn-eval-ground-truth');
    if (btnEval) {
      btnEval.addEventListener('click', async () => {
        if (window.jarvisAPI && window.jarvisAPI.evaluateVisualGroundTruth) {
          const res: any = await window.jarvisAPI.evaluateVisualGroundTruth();
          if (res && res.status === 'SUCCESS') {
            this.render(this.currentContext, res.evaluation);
          }
        }
      });
    }

    const elemItems = this.container.querySelectorAll('.visual-elem-item');
    elemItems.forEach((item) => {
      item.addEventListener('click', () => {
        const id = item.getAttribute('data-elem-id');
        if (this.currentContext && this.currentContext.elements) {
          this.selectedElement = this.currentContext.elements.find((e: any) => e.id === id);
          this.render(this.currentContext, this.currentEval);
        }
      });
    });
  }

  private async triggerAnalyze(scenario: string): Promise<void> {
    if (window.jarvisAPI && window.jarvisAPI.analyzeVisualScreen) {
      const res: any = await window.jarvisAPI.analyzeVisualScreen(scenario);
      if (res && res.status === 'SUCCESS') {
        this.render(res.visual_context);
      }
    }
  }
}
