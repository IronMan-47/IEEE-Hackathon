import { describe, it, expect, beforeEach, vi } from 'vitest';
import { IPCChannel } from '../../core/events/ipc-contracts';
import { TaskView } from '../../apps/desktop/renderer/components/task-view';

describe('Phase 15 — Grounded Agentic Task Orchestration Unit Tests', () => {
  let mockContainer: { innerHTML: string; querySelector: (sel: string) => any; addEventListener?: any };

  beforeEach(() => {
    mockContainer = {
      innerHTML: '',
      querySelector: (sel: string) => {
        if (mockContainer.innerHTML.includes(sel.replace('#', ''))) {
          return { addEventListener: vi.fn() };
        }
        return null;
      }
    };
    vi.stubGlobal('document', {
      getElementById: (id: string) => id === 'task-view-container' ? mockContainer : null
    });
  });

  it('defines Phase 15 IPC channels for task orchestration', () => {
    expect(IPCChannel.TASK_CREATE).toBe('jarvis:task-create');
    expect(IPCChannel.TASK_GET).toBe('jarvis:task-get');
    expect(IPCChannel.TASK_APPROVE_STEP).toBe('jarvis:task-approve-step');
    expect(IPCChannel.TASK_EXECUTE_STEP).toBe('jarvis:task-execute-step');
    expect(IPCChannel.TASK_PAUSE).toBe('jarvis:task-pause');
    expect(IPCChannel.TASK_CANCEL).toBe('jarvis:task-cancel');
    expect(IPCChannel.TASK_RESUME).toBe('jarvis:task-resume');
  });

  it('renders initial task creation view when task is null', () => {
    const taskView = new TaskView('task-view-container');
    taskView.render(null);

    expect(mockContainer.innerHTML).toContain('Phase 15 Grounded Agentic Task Orchestration');
    expect(mockContainer.innerHTML).toContain('task-input-prompt');
    expect(mockContainer.innerHTML).toContain('task-btn-create');
  });

  it('renders active task state and step approval controls', () => {
    const mockTask = {
      task_id: 'task_100',
      user_request: 'Change button color to blue on Living Canvas',
      status: 'AWAITING_APPROVAL',
      approval_policy: 'STEP_BY_STEP',
      budget: { max_steps: 10, max_replans: 3, current_steps: 0, current_replans: 0 },
      current_step_index: 0,
      last_context_hash: 'abc123456',
      steps: [
        {
          step_id: 'step_1',
          step_number: 1,
          step_type: 'EXECUTE',
          title: 'Execute Approved Action on LIVING_CANVAS',
          description: 'Modify button element color',
          target_domain: 'living_canvas',
          expected_postcondition: 'Button color updated to blue',
          status: 'AWAITING_APPROVAL',
          proposal: { proposal_id: 'prop_1', domain: 'living_canvas', risk: 'LOW' }
        }
      ]
    };

    const taskView = new TaskView('task-view-container');
    taskView.render(mockTask);

    expect(mockContainer.innerHTML).toContain('Task: "Change button color to blue on Living Canvas"');
    expect(mockContainer.innerHTML).toContain('STATUS: AWAITING_APPROVAL');
    expect(mockContainer.innerHTML).toContain('STEPS: 0/10');
    expect(mockContainer.innerHTML).toContain('task-btn-approve');
  });
});
