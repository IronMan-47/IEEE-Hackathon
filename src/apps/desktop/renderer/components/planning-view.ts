
function escapeHtml(unsafe: any): string {
  return String(unsafe)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
/**
 * JARVIS Phase 8 & 9 Planning View Component
 * Renders Context-Aware Intent Understanding & Non-Executable Structured Plan
 */

export class PlanningView {
  private container: HTMLElement;
  private currentPlanData: any = null;
  private currentClarificationData: any = null;
  private currentContextData: any = null;
  private onPlanAccepted?: (plan: any) => void;

  constructor(containerId: string, options?: { onPlanAccepted?: (plan: any) => void }) {
    const el = document.getElementById(containerId);
    if (!el) {
      throw new Error(`Container #${containerId} not found`);
    }
    this.container = el;
    this.onPlanAccepted = options?.onPlanAccepted;
  }

  public render(): void {
    this.container.innerHTML = `
      <div class="planning-view-card" style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 12px; padding: 20px; color: #f8fafc; font-family: sans-serif;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 12px;">
          <div>
            <h3 style="margin: 0; color: #38bdf8; font-size: 1.25rem;">Context-Aware Intent Understanding & Planning</h3>
            <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 0.85rem;">Phase 8 Strategy Engine · Read-Only Structured Planning Boundary</p>
          </div>
          <span style="background: #0369a1; color: #e0f2fe; padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600;">NO EXECUTION PRIMITIVES</span>
        </div>

        <!-- Request Input Area -->
        <div style="margin-bottom: 20px; display: flex; gap: 10px;">
          <input id="plan-user-input" type="text" placeholder="Enter request (e.g. 'Clean up this Python file and improve error handling')" style="flex: 1; background: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 10px 14px; color: #f8fafc; font-size: 0.9rem;" />
          <button id="btn-generate-plan" style="background: #0284c7; color: white; border: none; border-radius: 6px; padding: 10px 18px; font-weight: 600; cursor: pointer;">Generate Strategy Plan</button>
        </div>

        <!-- Dynamic Content Display -->
        <div id="plan-output-content">
          <div style="text-align: center; padding: 40px; color: #64748b;">
            <p style="margin: 0;">Enter a natural language request above to generate a context-aware plan.</p>
          </div>
        </div>
      </div>
    `;

    this.attachEvents();
  }

  private attachEvents(): void {
    const btn = this.container.querySelector('#btn-generate-plan');
    const input = this.container.querySelector('#plan-user-input') as HTMLInputElement;

    if (btn && input) {
      btn.addEventListener('click', async () => {
        const text = input.value.trim();
        if (!text) return;
        await this.handlePlanGeneration(text);
      });

      input.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter') {
          const text = input.value.trim();
          if (!text) return;
          await this.handlePlanGeneration(text);
        }
      });
    }
  }

  private async handlePlanGeneration(text: string): Promise<void> {
    const outputEl = this.container.querySelector('#plan-output-content');
    if (outputEl) {
      outputEl.innerHTML = `<div style="text-align: center; padding: 30px; color: #38bdf8;">Classifying Intent & Formulating Strategy Plan...</div>`;
    }

    try {
      if (window.jarvisAPI && window.jarvisAPI.generatePlan) {
        const res: any = await window.jarvisAPI.generatePlan(text);

        if (res.status === 'CLARIFICATION_REQUIRED') {
          this.renderClarification(res.clarification, res.context);
        } else if (res.status === 'SUCCESS') {
          this.currentPlanData = res.plan;
          this.currentContextData = res.context;
          this.renderPlan(res.plan, res.context, res.intent, res.goal);
        } else {
          if (outputEl) {
            outputEl.innerHTML = `<div style="color: #ef4444; padding: 16px; background: rgba(239, 68, 68, 0.1); border-radius: 6px;">Plan Error: ${escapeHtml(res.error || 'Unknown error')}</div>`;
          }
        }
      }
    } catch (err: any) {
      if (outputEl) {
        outputEl.innerHTML = `<div style="color: #ef4444; padding: 16px; background: rgba(239, 68, 68, 0.1); border-radius: 6px;">IPC Communication Failure: ${escapeHtml(String(err))}</div>`;
      }
    }
  }

  private renderClarification(clarification: any, context: any): void {
    const outputEl = this.container.querySelector('#plan-output-content');
    if (!outputEl) return;

    outputEl.innerHTML = `
      <div style="background: #1e293b; border: 1px solid #f59e0b; border-radius: 8px; padding: 16px; margin-top: 10px;">
        <div style="display: flex; align-items: center; gap: 8px; color: #f59e0b; font-weight: 700; margin-bottom: 8px;">
          <span>⚠️ Ambiguity Detected — Clarification Needed</span>
        </div>
        <p style="margin: 0 0 12px 0; color: #f8fafc; font-size: 0.95rem;">${clarification.question}</p>
        <div style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 12px;"><strong>Reason:</strong> ${clarification.reason}</div>
        <div style="background: #0f172a; padding: 10px; border-radius: 6px; font-size: 0.8rem; color: #cbd5e1;">
          <strong>Missing Information:</strong>
          <ul style="margin: 4px 0 0 16px; padding: 0;">
            ${clarification.missing_information.map((item: string) => `<li>${item}</li>`).join('')}
          </ul>
        </div>
      </div>
    `;
  }

  private renderPlan(plan: any, context: any, intent: any, goal: any): void {
    const outputEl = this.container.querySelector('#plan-output-content');
    if (!outputEl) return;

    const constraints = plan.constraints || [];
    const steps = plan.steps || [];
    const isAccepted = plan.status === 'ACCEPTED';

    outputEl.innerHTML = `
      <div style="display: grid; grid-template-columns: 1fr; gap: 16px; margin-top: 10px;">
        
        <!-- Application & Context Header -->
        <div style="background: #1e293b; border-radius: 8px; padding: 12px 16px; border: 1px solid #334155;">
          <span style="color: #64748b; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">Active Application Context</span>
          <div style="color: #38bdf8; font-weight: 600; font-size: 0.95rem; margin-top: 4px;">
            ${context.active_app_domain.toUpperCase()} · ${context.active_app_name} · ${context.active_file || context.active_window_title}
          </div>
        </div>

        <!-- Intent & Goal Grid -->
        <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 12px;">
          <div style="background: #1e293b; border-radius: 8px; padding: 12px 16px; border: 1px solid #334155;">
            <span style="color: #64748b; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">Classified Intent</span>
            <div style="margin-top: 6px; display: flex; align-items: center; gap: 8px;">
              <span style="background: #0284c7; color: white; padding: 4px 10px; border-radius: 4px; font-weight: 700; font-size: 0.85rem;">${intent.intent_type}</span>
              <span style="color: #94a3b8; font-size: 0.75rem;">(${intent.confidence} Confidence)</span>
            </div>
          </div>

          <div style="background: #1e293b; border-radius: 8px; padding: 12px 16px; border: 1px solid #334155;">
            <span style="color: #64748b; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">Primary Goal</span>
            <div style="color: #f8fafc; font-weight: 600; font-size: 0.9rem; margin-top: 4px;">${goal.primary_goal}</div>
          </div>
        </div>

        <!-- Active Constraints -->
        <div style="background: #1e293b; border-radius: 8px; padding: 12px 16px; border: 1px solid #334155;">
          <span style="color: #64748b; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">Active Constraints</span>
          <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;">
            ${constraints.map((c: any) => `
              <span style="background: rgba(148, 163, 184, 0.1); border: 1px solid rgba(148, 163, 184, 0.2); color: #cbd5e1; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem;">
                • ${c.type} (${c.source})
              </span>
            `).join('')}
          </div>
        </div>

        <!-- Non-Executable Structured Plan Steps -->
        <div style="background: #1e293b; border-radius: 8px; padding: 16px; border: 1px solid #334155;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="color: #38bdf8; font-size: 0.9rem; font-weight: 700; text-transform: uppercase;">Formulated Strategy Plan (${plan.steps.length} Steps)</span>
            <span style="font-size: 0.75rem; color: #94a3b8;">Plan ID: ${escapeHtml(plan.plan_id)} (v${plan.version}) · Author: ${plan.author}</span>
          </div>

          <div style="display: flex; flex-direction: column; gap: 8px;">
            ${steps.map((step: any, idx: number) => `
              <div style="background: #0f172a; padding: 10px 14px; border-radius: 6px; border-left: 3px solid #0284c7; display: flex; align-items: center; justify-content: space-between;">
                <div>
                  <span style="color: #38bdf8; font-weight: 700; margin-right: 8px;">${idx + 1}.</span>
                  <span style="color: #f8fafc; font-size: 0.9rem;">${step.description}</span>
                </div>
                <span style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 700;">${step.type}</span>
              </div>
            `).join('')}
          </div>

          <div style="margin-top: 14px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.05); font-size: 0.8rem; color: #94a3b8;">
            <strong>Rationale:</strong> ${plan.reasoning_summary}
          </div>
        </div>

        <!-- Action Control Buttons (NO EXECUTION BUTTON) -->
        <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 8px;">
          <button id="btn-reject-plan" style="background: #334155; color: #f8fafc; border: none; border-radius: 6px; padding: 10px 18px; font-weight: 600; cursor: pointer;">Reject</button>
          <button id="btn-edit-plan" style="background: #475569; color: #f8fafc; border: none; border-radius: 6px; padding: 10px 18px; font-weight: 600; cursor: pointer;">Edit Plan</button>
          <button id="btn-accept-plan" style="background: ${isAccepted ? '#059669' : '#0284c7'}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: 700; cursor: pointer;">
            ${isAccepted ? '✓ Strategy Accepted' : 'Accept Plan & Propose'}
          </button>
        </div>

      </div>
    `;

    this.attachActionEvents(plan);
  }

  private attachActionEvents(plan: any): void {
    const btnAccept = this.container.querySelector('#btn-accept-plan');
    const btnReject = this.container.querySelector('#btn-reject-plan');
    const btnEdit = this.container.querySelector('#btn-edit-plan');

    if (btnAccept) {
      btnAccept.addEventListener('click', async () => {
        if (window.jarvisAPI && window.jarvisAPI.acceptPlan) {
          const res: any = await window.jarvisAPI.acceptPlan(plan);
          if (res.status === 'SUCCESS') {
            this.currentPlanData = res.plan;
            this.renderPlan(res.plan, this.currentContextData, { intent_type: plan.intent, confidence: 'HIGH' }, plan.goal);
            if (this.onPlanAccepted) {
              this.onPlanAccepted(res.plan);
            }
          }
        }
      });
    }

    if (btnReject) {
      btnReject.addEventListener('click', () => {
        const outputEl = this.container.querySelector('#plan-output-content');
        if (outputEl) {
          outputEl.innerHTML = `<div style="color: #94a3b8; text-align: center; padding: 40px;">Plan rejected. Enter a new request above.</div>`;
        }
      });
    }

    if (btnEdit) {
      btnEdit.addEventListener('click', async () => {
        const modifiedSteps = [...plan.steps];
        modifiedSteps.push({
          id: `step_${modifiedSteps.length + 1}`,
          type: 'VERIFY',
          description: 'Human-requested additional verification step',
          reason: 'Human plan edit'
        });

        if (window.jarvisAPI && window.jarvisAPI.modifyPlan) {
          const res: any = await window.jarvisAPI.modifyPlan(plan, modifiedSteps);
          if (res.status === 'SUCCESS') {
            this.currentPlanData = res.plan;
            this.renderPlan(res.plan, this.currentContextData, { intent_type: plan.intent, confidence: 'HIGH' }, plan.goal);
          }
        }
      });
    }
  }
}
