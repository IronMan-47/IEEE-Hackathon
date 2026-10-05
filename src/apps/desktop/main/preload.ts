import { contextBridge, ipcRenderer } from 'electron';
import {
  IPCChannel,
  StatusChangedPayload,
  ErrorNotificationPayload,
  JarvisConfigPayload,
  JarvisElectronAPI
} from '../../../core/events/ipc-contracts';

const api: JarvisElectronAPI = {
  onStatusChanged: (callback: (payload: StatusChangedPayload) => void) => {
    const handler = (_event: unknown, payload: StatusChangedPayload) => callback(payload);
    ipcRenderer.on(IPCChannel.STATUS_CHANGED, handler);
    return () => ipcRenderer.removeListener(IPCChannel.STATUS_CHANGED, handler);
  },

  onShowOverlay: (callback: () => void) => {
    const handler = () => callback();
    ipcRenderer.on(IPCChannel.SHOW_OVERLAY, handler);
    return () => ipcRenderer.removeListener(IPCChannel.SHOW_OVERLAY, handler);
  },

  onHideOverlay: (callback: () => void) => {
    const handler = () => callback();
    ipcRenderer.on(IPCChannel.HIDE_OVERLAY, handler);
    return () => ipcRenderer.removeListener(IPCChannel.HIDE_OVERLAY, handler);
  },

  onErrorNotification: (callback: (payload: ErrorNotificationPayload) => void) => {
    const handler = (_event: unknown, payload: ErrorNotificationPayload) => callback(payload);
    ipcRenderer.on(IPCChannel.ERROR_NOTIFICATION, handler);
    return () => ipcRenderer.removeListener(IPCChannel.ERROR_NOTIFICATION, handler);
  },

  requestToggle: async () => {
    await ipcRenderer.invoke(IPCChannel.REQUEST_TOGGLE);
  },

  requestEmergencyStop: async () => {
    await ipcRenderer.invoke(IPCChannel.REQUEST_EMERGENCY_STOP);
  },

  requestReactivate: async () => {
    await ipcRenderer.invoke(IPCChannel.REQUEST_REACTIVATE);
  },

  getState: async () => {
    return await ipcRenderer.invoke(IPCChannel.REQUEST_GET_STATE);
  },

  getConfig: async () => {
    return await ipcRenderer.invoke(IPCChannel.REQUEST_GET_CONFIG);
  },

  requestHide: async () => {
    await ipcRenderer.invoke(IPCChannel.REQUEST_HIDE);
  },

  requestQuit: async () => {
    await ipcRenderer.invoke(IPCChannel.REQUEST_QUIT);
  },

  requestIgnoreMouseEvents: async (ignore: boolean) => {
    await ipcRenderer.invoke(IPCChannel.REQUEST_IGNORE_MOUSE_EVENTS, ignore);
  },

  // Phase 2 Canvas API Implementation
  getCanvasState: async () => {
    return await ipcRenderer.invoke(IPCChannel.CANVAS_GET_STATE);
  },

  generateProposal: async (userText?: string) => {
    return await ipcRenderer.invoke(IPCChannel.CANVAS_GENERATE_PROPOSAL, userText);
  },

  acceptProposal: async () => {
    return await ipcRenderer.invoke(IPCChannel.CANVAS_ACCEPT_PROPOSAL);
  },

  rejectProposal: async (reason?: string) => {
    return await ipcRenderer.invoke(IPCChannel.CANVAS_REJECT_PROPOSAL, reason);
  },

  modifyProposal: async (ops: unknown[]) => {
    return await ipcRenderer.invoke(IPCChannel.CANVAS_MODIFY_PROPOSAL, ops);
  },

  mutateCanvasManual: async () => {
    return await ipcRenderer.invoke(IPCChannel.CANVAS_MUTATE_MANUAL);
  },

  // Phase 5 Version Graph API Methods
  getVersionHistory: async () => {
    return await ipcRenderer.invoke(IPCChannel.VERSION_GET_HISTORY);
  },

  getBranches: async () => {
    return await ipcRenderer.invoke(IPCChannel.VERSION_GET_BRANCHES);
  },

  createBranch: async (name: string, fromVersionId?: string) => {
    return await ipcRenderer.invoke(IPCChannel.VERSION_CREATE_BRANCH, name, fromVersionId);
  },

  switchBranch: async (branchId: string, force?: boolean) => {
    return await ipcRenderer.invoke(IPCChannel.VERSION_SWITCH_BRANCH, branchId, force);
  },

  checkoutVersion: async (versionId: string, force?: boolean) => {
    return await ipcRenderer.invoke(IPCChannel.VERSION_CHECKOUT, versionId, force);
  },

  rollbackToVersion: async (versionId: string) => {
    return await ipcRenderer.invoke(IPCChannel.VERSION_ROLLBACK, versionId);
  },

  diffVersions: async (vIdA: string, vIdB: string) => {
    return await ipcRenderer.invoke(IPCChannel.VERSION_DIFF, vIdA, vIdB);
  },

  commitDirty: async (message?: string) => {
    return await ipcRenderer.invoke(IPCChannel.VERSION_COMMIT_DIRTY, message);
  },

  discardDirty: async () => {
    return await ipcRenderer.invoke(IPCChannel.VERSION_DISCARD_DIRTY);
  },

  // Phase 6 & 7 Perception & Application Context API Methods
  perceiveDesktop: async (requestCapture: boolean = true) => {
    return await ipcRenderer.invoke(IPCChannel.PERCEIVE_DESKTOP, requestCapture);
  },

  togglePerceptionPolicy: async (enabled: boolean) => {
    return await ipcRenderer.invoke(IPCChannel.PERCEIVE_POLICY_TOGGLE, enabled);
  },

  getApplicationContext: async () => {
    return await ipcRenderer.invoke(IPCChannel.PERCEIVE_GET_APP_CONTEXT);
  },

  // Phase 8 Planning API Methods
  generatePlan: async (userText: string) => {
    return await ipcRenderer.invoke(IPCChannel.PLAN_GENERATE, userText);
  },

  modifyPlan: async (originalPlan: unknown, newSteps: unknown[]) => {
    return await ipcRenderer.invoke(IPCChannel.PLAN_MODIFY, originalPlan, newSteps);
  },

  acceptPlan: async (plan: unknown) => {
    return await ipcRenderer.invoke(IPCChannel.PLAN_ACCEPT, plan);
  },

  // Phase 9 Proposal Review API Methods
  generateProposalFromPlan: async (plan: unknown) => {
    return await ipcRenderer.invoke(IPCChannel.PROPOSAL_GENERATE_FROM_PLAN, plan);
  },

  modifyProposalPhase9: async (originalProposal: unknown, modifiedOps: unknown[]) => {
    return await ipcRenderer.invoke(IPCChannel.PROPOSAL_MODIFY_PHASE9, originalProposal, modifiedOps);
  },

  acceptProposalPhase9: async (proposal: unknown) => {
    return await ipcRenderer.invoke(IPCChannel.PROPOSAL_ACCEPT_PHASE9, proposal);
  },

  // Phase 10 Controlled Execution API Method
  executeProposal: async (proposal: unknown, approvalToken: unknown) => {
    return await ipcRenderer.invoke(IPCChannel.EXECUTE_PROPOSAL, proposal, approvalToken);
  },

  // Phase 13 Visual Perception API Methods
  analyzeVisualScreen: async (scenario?: string) => {
    return await ipcRenderer.invoke(IPCChannel.VISUAL_ANALYZE_SCREEN, scenario);
  },

  getVisualContext: async () => {
    return await ipcRenderer.invoke(IPCChannel.VISUAL_GET_CURRENT_CONTEXT);
  },

  clearVisualContext: async () => {
    return await ipcRenderer.invoke(IPCChannel.VISUAL_CLEAR_CONTEXT);
  },

  evaluateVisualGroundTruth: async () => {
    return await ipcRenderer.invoke(IPCChannel.VISUAL_EVALUATE_GROUND_TRUTH);
  },

  // Phase 15 Task Orchestration API Methods
  createTask: async (text: string, maxSteps?: number, maxReplans?: number) => {
    return await ipcRenderer.invoke(IPCChannel.TASK_CREATE, text, maxSteps, maxReplans);
  },

  getTask: async (taskId: string) => {
    return await ipcRenderer.invoke(IPCChannel.TASK_GET, taskId);
  },

  approveTaskStep: async (taskId: string, stepId: string) => {
    return await ipcRenderer.invoke(IPCChannel.TASK_APPROVE_STEP, taskId, stepId);
  },

  executeTaskStep: async (taskId: string, stepId: string) => {
    return await ipcRenderer.invoke(IPCChannel.TASK_EXECUTE_STEP, taskId, stepId);
  },

  pauseTask: async (taskId: string) => {
    return await ipcRenderer.invoke(IPCChannel.TASK_PAUSE, taskId);
  },

  cancelTask: async (taskId: string) => {
    return await ipcRenderer.invoke(IPCChannel.TASK_CANCEL, taskId);
  },

  resumeTask: async (taskId: string) => {
    return await ipcRenderer.invoke(IPCChannel.TASK_RESUME, taskId);
  },

  // Phase 16 Explainability & Human-in-the-Loop API Methods
  getTaskExplanation: async (taskId: string, depth?: string) => {
    return await ipcRenderer.invoke(IPCChannel.TASK_GET_EXPLANATION, taskId, depth);
  },
  modifyTaskStep: async (taskId: string, stepId: string, instructions: string) => {
    return await ipcRenderer.invoke(IPCChannel.TASK_MODIFY_STEP, taskId, stepId, instructions);
  },

  // Phase 17 Agent Runtime API Methods
  getRuntimeState: async () => {
    return await ipcRenderer.invoke(IPCChannel.RUNTIME_GET_STATE);
  },
  recoverRuntime: async (action: string, domain?: string) => {
    return await ipcRenderer.invoke(IPCChannel.RUNTIME_RECOVER, action, domain);
  },
  getRuntimeEvents: async (limit?: number) => {
    return await ipcRenderer.invoke(IPCChannel.RUNTIME_GET_EVENTS, limit);
  },

  // Phase 18 Voice API Methods
  startVoiceListening: async () => {
    return await ipcRenderer.invoke(IPCChannel.VOICE_START);
  },
  stopVoiceListening: async () => {
    return await ipcRenderer.invoke(IPCChannel.VOICE_STOP);
  },
  processVoiceSpeech: async (text: string, confidence?: string) => {
    return await ipcRenderer.invoke(IPCChannel.VOICE_PROCESS, text, confidence);
  },
  confirmVoiceTranscript: async (transcriptId: string, text: string) => {
    return await ipcRenderer.invoke(IPCChannel.VOICE_CONFIRM, transcriptId, text);
  },
  cancelVoiceSession: async () => {
    return await ipcRenderer.invoke(IPCChannel.VOICE_CANCEL);
  }
};

contextBridge.exposeInMainWorld('jarvisAPI', api);
