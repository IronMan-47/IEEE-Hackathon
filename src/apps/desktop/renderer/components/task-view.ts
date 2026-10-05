
function escapeHtml(unsafe: any): string {
  return String(unsafe)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
/**
 * JARVIS Phase 15 — Grounded Agentic Task Orchestration View Component
 * Renders Multi-Step Workflow Execution, Step Approval Controls, Budget Counters,
 * Step-by-step Timeline, Reassessment Status, and Pause/Cancel/Resume Controls.
 */

export interface TaskViewOptions {
  onTaskUpdated?: (task: any) => void;
}

export class TaskView {
  private container: HTMLElement;
  private currentTask: any = null;
  private isProcessing: boolean = false;
  private options?: TaskViewOptions;

  constructor(containerId: string, options?: TaskViewOptions) {
    const el = document.getElementById(containerId);
    if (!el) {
      throw new Error(`Container #${containerId} not found`);
    }
    this.container = el;
    this.options = options;
  }

  public render(task: any = null): void {
    this.currentTask = task;

    if (!task) {
      this.container.innerHTML = `
        <div style="background: rgba(15, 23, 42, 0.9); border: 1px dashed rgba(56, 189, 248, 0.3); border-radius: 12px; padding: 24px; color: #64748b; text-align: center; font-family: sans-serif;">
          <h4 style="margin: 0 0 8px 0; color: #38bdf8; font-size: 1rem;">Phase 15 Grounded Agentic Task Orchestration</h4>
          <p style="margin: 0 0 16px 0; font-size: 0.85rem;">Execute multi-step workflows with strict step-by-step human approval, context reassessment, and budget controls.</p>
          <div style="display: flex; gap: 8px; justify-content: center;">
            <input type="text" id="task-input-prompt" placeholder="e.g. Change button color to blue on Living Canvas" style="width: 70%; padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.2); background: rgba(0,0,0,0.4); color: white; font-size: 0.85rem;" />
            <button id="task-btn-create" style="background: #0284c7; color: white; border: none; padding: 8px 16px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 0.85rem;">Start Task</button>
          </div>
        </div>
      `;
      this.attachInputListeners();
      return;
    }

    const statusColor = this.getStatusColor(task.status);
    const budget = task.budget || { max_steps: 10, max_replans: 3, current_steps: 0, current_replans: 0 };
    const currentStep = task.steps && task.steps[task.current_step_index];
    const isAwaitingApproval = task.status === 'AWAITING_APPROVAL';
    const isApproved = currentStep && currentStep.approval_token && currentStep.status === 'APPROVED';

    this.container.innerHTML = `
      <div class="task-orchestration-card" style="background: rgba(15, 23, 42, 0.95); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 12px; padding: 20px; color: #f8fafc; font-family: sans-serif; margin-top: 16px;">
        
        <!-- Task Header -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px;">
          <div>
            <span style="color: #64748b; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">Phase 15 Grounded Task Orchestration</span>
            <h3 style="margin: 2px 0 0 0; color: #38bdf8; font-size: 1.15rem;">Task: "${task.user_request}"</h3>
          </div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="background: ${statusColor}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;">STATUS: ${escapeHtml(task.status)}</span>
            <span style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;">STEPS: ${budget.current_steps}/${budget.max_steps}</span>
            <span style="background: rgba(245, 158, 11, 0.15); color: #f59e0b; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;">REPLANS: ${budget.current_replans}/${budget.max_replans}</span>
          </div>
        </div>

        ${task.error ? `
          <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid #ef4444; border-radius: 8px; padding: 10px; color: #fca5a5; font-size: 0.85rem; margin-bottom: 14px;">
            ⚠️ <strong>Error / Block:</strong> ${task.error}
          </div>
        ` : ''}

        
        <!-- Explanation Panel (Phase 16) -->
        ${task.explanation ? `
          <div style="background: rgba(30, 41, 59, 0.9); border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 10px; padding: 14px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px; margin-bottom: 8px;">
              <span style="color: #38bdf8; font-size: 0.85rem; font-weight: 700;">AGENT EXPLANATION</span>
              <div>
                <select id="explanation-depth-select" style="background: #0f172a; color: #94a3b8; border: 1px solid #334155; border-radius: 4px; font-size: 0.75rem; padding: 2px 6px;">
                  <option value="COMPACT">Compact</option>
                  <option value="STANDARD" selected>Standard</option>
                  <option value="DETAILED">Detailed</option>
                </select>
              </div>
            </div>
            <div id="explanation-content" style="color: #cbd5e1; font-size: 0.85rem;">
               <p style="margin: 0 0 4px 0"><strong>Summary:</strong> ${task.explanation.summary}</p>
               <p style="margin: 0 0 4px 0"><strong>Reasoning:</strong> ${task.explanation.reason}</p>
               ${task.explanation.risk ? `<p style="margin: 0 0 4px 0; color: #f87171"><strong>Risk (${task.explanation.risk.level}):</strong> ${task.explanation.risk.reason}</p>` : ''}
            </div>
          </div>
        ` : ''}
        
        <!-- Blocked / Verification Panel -->
        ${task.status === 'BLOCKED' || task.status === 'FAILED' ? `
          <div style="background: rgba(220, 38, 38, 0.15); border: 1px solid #ef4444; border-radius: 10px; padding: 14px; margin-bottom: 16px;">
            <h4 style="margin: 0 0 8px 0; color: #fca5a5; font-size: 0.95rem;">Why Did JARVIS Stop?</h4>
            <p style="margin: 0; color: #fecaca; font-size: 0.85rem;">${task.error || 'Execution blocked or verification failed.'}</p>
          </div>
        ` : ''}

        <!-- Active Step Panel -->
        ${currentStep ? `
          <div style="background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 10px; padding: 14px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="color: #94a3b8; font-size: 0.8rem; font-weight: 600;">ACTIVE STEP ${task.current_step_index + 1} OF ${task.steps.length} (${currentStep.step_type})</span>
              <span style="color: #38bdf8; font-size: 0.8rem;">Domain: <strong>${currentStep.target_domain || 'N/A'}</strong></span>
            </div>
            <h4 style="margin: 6px 0; color: #f8fafc; font-size: 0.95rem;">${currentStep.title}</h4>
            <p style="margin: 0 0 10px 0; color: #cbd5e1; font-size: 0.85rem;">${currentStep.description}</p>
            
            ${currentStep.expected_postcondition ? `
              <div style="color: #64748b; font-size: 0.8rem; margin-bottom: 8px;">
                🎯 <strong>Expected Postcondition:</strong> ${currentStep.expected_postcondition}
              </div>
            ` : ''}

            <!-- Step Action Buttons -->
            <div style="display: flex; gap: 10px; margin-top: 12px;">
              
              ${isAwaitingApproval ? `
                <button id="task-btn-approve" style="background: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 0.85rem;">
                  Approve Step ${task.current_step_index + 1}
                </button>
                <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);">
                  <select id="task-modify-select" style="background: #0f172a; color: #cbd5e1; border: 1px solid #334155; border-radius: 4px; padding: 6px; font-size: 0.8rem; margin-right: 8px;">
                    <option value="">-- Modify Step --</option>
                    <option value="Change target element">Change target element</option>
                    <option value="Use a different method">Use a different method</option>
                    <option value="Skip this step">Skip this step</option>
                  </select>
                  <input type="text" id="task-input-modify" placeholder="Or type instruction..." style="background: rgba(0,0,0,0.3); border: 1px solid #334155; padding: 6px; border-radius: 4px; color: #fff; font-size: 0.8rem;" />
                  <button id="task-btn-modify" style="background: #f59e0b; color: white; border: none; padding: 6px 12px; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 0.8rem; margin-left: 8px;">Submit Correction</button>
                </div>
              ` : ''}


              ${isApproved ? `
                <button id="task-btn-execute" style="background: #0284c7; color: white; border: none; padding: 8px 16px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 0.85rem;">
                  ⚡ Execute Step ${task.current_step_index + 1} with Approval Token
                </button>
              ` : ''}
            </div>
          </div>
        ` : ''}

        <!-- Steps Timeline -->
        <h4 style="margin: 0 0 10px 0; color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em;">Task Workflow Plan</h4>
        <div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px;">
          ${task.steps ? task.steps.map((step: any, idx: number) => `
            <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid ${idx === task.current_step_index ? '#38bdf8' : 'rgba(255,255,255,0.08)'}; border-radius: 8px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center;">
              <div>
                <span style="font-weight: 700; color: ${idx === task.current_step_index ? '#38bdf8' : '#94a3b8'}; font-size: 0.85rem;">Step ${idx + 1}: ${step.title}</span>
                <div style="font-size: 0.75rem; color: #64748b; margin-top: 2px;">Type: ${step.step_type} | Domain: ${step.target_domain || 'N/A'}</div>
              </div>
              <div>
                <span style="background: ${this.getStepStatusBg(step.status)}; color: white; font-size: 0.7rem; padding: 3px 8px; border-radius: 10px; font-weight: 600;">${escapeHtml(step.status)}</span>
              </div>
            </div>
          `).join('') : '<p style="color: #64748b;">No steps generated.</p>'}
        </div>

        <!-- Task Control Toolbar -->
        <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px;">
          <div style="display: flex; gap: 8px;">
            ${task.status === 'PAUSED' ? `
              <button id="task-btn-resume" style="background: #3b82f6; color: white; border: none; padding: 6px 12px; border-radius: 6px; font-size: 0.8rem; cursor: pointer;">Resume Task</button>
            ` : task.status !== 'COMPLETED' && task.status !== 'FAILED' && task.status !== 'CANCELLED' ? `
              <button id="task-btn-pause" style="background: #f59e0b; color: white; border: none; padding: 6px 12px; border-radius: 6px; font-size: 0.8rem; cursor: pointer;">Pause Task</button>
            ` : ''}

            ${task.status !== 'COMPLETED' && task.status !== 'CANCELLED' ? `
              <button id="task-btn-cancel" style="background: #ef4444; color: white; border: none; padding: 6px 12px; border-radius: 6px; font-size: 0.8rem; cursor: pointer;">Cancel Task</button>
            ` : ''}
          </div>
          <span style="font-size: 0.75rem; color: #64748b;">Context Hash: <code>${task.last_context_hash ? task.last_context_hash.slice(0, 8) : 'N/A'}</code></span>
        </div>

      </div>
    `;

    this.attachTaskControlListeners();
  }

  private attachInputListeners(): void {
    const btnCreate = document.getElementById('task-btn-create');
    const inputPrompt = document.getElementById('task-input-prompt') as HTMLInputElement;

    btnCreate?.addEventListener('click', async () => {
      const text = inputPrompt?.value?.trim();
      if (!text || !window.jarvisAPI?.createTask) return;
      try {
        const res: any = await window.jarvisAPI.createTask(text);
        if (res && res.status === 'SUCCESS' && res.task) {
          this.render(res.task);
          this.options?.onTaskUpdated?.(res.task);
        }
      } catch (err) {
        console.error('Task creation failed:', err);
      }
    });
  }

  private attachTaskControlListeners(): void {
    const btnApprove = document.getElementById('task-btn-approve');
    const btnExecute = document.getElementById('task-btn-execute');
    const btnPause = document.getElementById('task-btn-pause');
    const btnCancel = document.getElementById('task-btn-cancel');
    const btnResume = document.getElementById('task-btn-resume');

const btnModify = document.getElementById('task-btn-modify');
    const inputModify = document.getElementById('task-input-modify') as HTMLInputElement;
    const selectModify = document.getElementById('task-modify-select') as HTMLSelectElement;

    btnModify?.addEventListener('click', async () => {
      if (!this.currentTask || !window.jarvisAPI?.modifyTaskStep) return;
      const instruction = inputModify?.value?.trim() || selectModify?.value;
      if (!instruction) return;

      const currentStep = this.currentTask.steps[this.currentTask.current_step_index];
      try {
        const res: any = await window.jarvisAPI.modifyTaskStep(this.currentTask.task_id, currentStep.step_id, instruction);
        if (res && res.status === 'SUCCESS' && res.task) {
          this.render(res.task);
          this.options?.onTaskUpdated?.(res.task);
        }
      } catch (err) {
        console.error('Step modification failed:', err);
      }
    });

    btnApprove?.addEventListener('click', async () => {
      if (!this.currentTask || !window.jarvisAPI?.approveTaskStep) return;
      const currentStep = this.currentTask.steps[this.currentTask.current_step_index];
      try {
        const res: any = await window.jarvisAPI.approveTaskStep(this.currentTask.task_id, currentStep.step_id);
        if (res && res.status === 'SUCCESS' && res.task) {
          this.render(res.task);
          this.options?.onTaskUpdated?.(res.task);
        }
      } catch (err) {
        console.error('Step approval failed:', err);
      }
    });

    btnExecute?.addEventListener('click', async () => {
      if (!this.currentTask || !window.jarvisAPI?.executeTaskStep) return;
      const currentStep = this.currentTask.steps[this.currentTask.current_step_index];
      try {
        const res: any = await window.jarvisAPI.executeTaskStep(this.currentTask.task_id, currentStep.step_id);
        if (res && res.status === 'SUCCESS' && res.task) {
          this.render(res.task);
          this.options?.onTaskUpdated?.(res.task);
        }
      } catch (err) {
        console.error('Step execution failed:', err);
      }
    });

    btnPause?.addEventListener('click', async () => {
      if (!this.currentTask || !window.jarvisAPI?.pauseTask) return;
      try {
        const res: any = await window.jarvisAPI.pauseTask(this.currentTask.task_id);
        if (res && res.status === 'SUCCESS' && res.task) {
          this.render(res.task);
          this.options?.onTaskUpdated?.(res.task);
        }
      } catch (err) {
        console.error('Task pause failed:', err);
      }
    });

    btnCancel?.addEventListener('click', async () => {
      if (!this.currentTask || !window.jarvisAPI?.cancelTask) return;
      try {
        const res: any = await window.jarvisAPI.cancelTask(this.currentTask.task_id);
        if (res && res.status === 'SUCCESS' && res.task) {
          this.render(res.task);
          this.options?.onTaskUpdated?.(res.task);
        }
      } catch (err) {
        console.error('Task cancel failed:', err);
      }
    });

    btnResume?.addEventListener('click', async () => {
      if (!this.currentTask || !window.jarvisAPI?.resumeTask) return;
      try {
        const res: any = await window.jarvisAPI.resumeTask(this.currentTask.task_id);
        if (res && res.status === 'SUCCESS' && res.task) {
          this.render(res.task);
          this.options?.onTaskUpdated?.(res.task);
        }
      } catch (err) {
        console.error('Task resume failed:', err);
      }
    });
  }

  private getStatusColor(status: string): string {
    switch (status) {
      case 'COMPLETED': return '#10b981';
      case 'AWAITING_APPROVAL': return '#f59e0b';
      case 'EXECUTING': return '#0284c7';
      case 'VERIFYING': return '#8b5cf6';
      case 'REASSESSING': return '#06b6d4';
      case 'PAUSED': return '#eab308';
      case 'BLOCKED': case 'FAILED': return '#ef4444';
      case 'CANCELLED': return '#64748b';
      default: return '#3b82f6';
    }
  }

  private getStepStatusBg(status: string): string {
    switch (status) {
      case 'COMPLETED': return '#10b981';
      case 'APPROVED': return '#059669';
      case 'AWAITING_APPROVAL': return '#d97706';
      case 'EXECUTING': case 'VERIFYING': return '#0284c7';
      case 'FAILED': case 'BLOCKED': return '#dc2626';
      case 'SKIPPED': return '#475569';
      default: return '#334155';
    }
  }
}
