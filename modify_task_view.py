import re

with open(r'c:\Users\lenovo\OneDrive\Desktop\Hackathons\Jarvis - Living Assistent\src\apps\desktop\renderer\components\task-view.ts', 'r', encoding='utf-8') as f:
    content = f.read()

explanation_ui = """
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
"""

content = content.replace("<!-- Active Step Panel -->", explanation_ui + "\n        <!-- Active Step Panel -->")

modification_ui = """
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
"""

content = re.sub(r'\$\{isAwaitingApproval \? `\s*<button id="task-btn-approve"[^>]*>.*?<\/button>\s*` : \'\'\}', modification_ui, content, flags=re.DOTALL)

listeners_code = "    btnApprove?.addEventListener('click', async () => {"

new_listeners_code = """
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
"""

content = content.replace(listeners_code, new_listeners_code.strip())

with open(r'c:\Users\lenovo\OneDrive\Desktop\Hackathons\Jarvis - Living Assistent\src\apps\desktop\renderer\components\task-view.ts', 'w', encoding='utf-8') as f:
    f.write(content)
