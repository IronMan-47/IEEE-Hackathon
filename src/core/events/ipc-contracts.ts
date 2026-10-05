import { JarvisState } from '../state/types';

/**
 * IPC Channel Identifiers
 */
export enum IPCChannel {
  // Main -> Renderer Events
  STATUS_CHANGED = 'jarvis:status-changed',
  SHOW_OVERLAY = 'jarvis:show-overlay',
  HIDE_OVERLAY = 'jarvis:hide-overlay',
  ERROR_NOTIFICATION = 'jarvis:error-notification',

  // Renderer -> Main Events
  REQUEST_TOGGLE = 'jarvis:request-toggle',
  REQUEST_EMERGENCY_STOP = 'jarvis:request-emergency-stop',
  REQUEST_REACTIVATE = 'jarvis:request-reactivate',
  REQUEST_GET_STATE = 'jarvis:get-state',
  REQUEST_GET_CONFIG = 'jarvis:get-config',
  REQUEST_HIDE = 'jarvis:request-hide',
  REQUEST_QUIT = 'jarvis:request-quit',
  REQUEST_IGNORE_MOUSE_EVENTS = 'jarvis:request-ignore-mouse-events',

  // Phase 2 Living Canvas IPC Channels
  CANVAS_GET_STATE = 'jarvis:canvas-get-state',
  CANVAS_GENERATE_PROPOSAL = 'jarvis:canvas-generate-proposal',
  CANVAS_ACCEPT_PROPOSAL = 'jarvis:canvas-accept-proposal',
  CANVAS_REJECT_PROPOSAL = 'jarvis:canvas-reject-proposal',
  CANVAS_MODIFY_PROPOSAL = 'jarvis:canvas-modify-proposal',
  CANVAS_MUTATE_MANUAL = 'jarvis:canvas-mutate-manual',

  // Phase 5 Version Graph IPC Channels
  VERSION_GET_HISTORY = 'jarvis:version-get-history',
  VERSION_GET_BRANCHES = 'jarvis:version-get-branches',
  VERSION_CREATE_BRANCH = 'jarvis:version-create-branch',
  VERSION_SWITCH_BRANCH = 'jarvis:version-switch-branch',
  VERSION_CHECKOUT = 'jarvis:version-checkout',
  VERSION_ROLLBACK = 'jarvis:version-rollback',
  VERSION_DIFF = 'jarvis:version-diff',
  VERSION_COMMIT_DIRTY = 'jarvis:version-commit-dirty',
  VERSION_DISCARD_DIRTY = 'jarvis:version-discard-dirty',

  // Phase 6 & 7 Perception & Application Context IPC Channels
  PERCEIVE_DESKTOP = 'jarvis:perceive-desktop',
  PERCEIVE_POLICY_TOGGLE = 'jarvis:perceive-policy-toggle',
  PERCEIVE_GET_APP_CONTEXT = 'jarvis:perceive-get-app-context',

  // Phase 8 Planning Pipeline IPC Channels
  PLAN_GENERATE = 'jarvis:plan-generate',
  PLAN_MODIFY = 'jarvis:plan-modify',
  PLAN_ACCEPT = 'jarvis:plan-accept',

  // Phase 9 Proposal Review IPC Channels
  PROPOSAL_GENERATE_FROM_PLAN = 'jarvis:proposal-generate-from-plan',
  PROPOSAL_MODIFY_PHASE9 = 'jarvis:proposal-modify-phase9',
  PROPOSAL_ACCEPT_PHASE9 = 'jarvis:proposal-accept-phase9',

  // Phase 10 Controlled Execution IPC Channel
  EXECUTE_PROPOSAL = 'jarvis:execute-proposal',

  // Phase 13 Visual Perception IPC Channels
  VISUAL_ANALYZE_SCREEN = 'jarvis:visual-analyze-screen',
  VISUAL_GET_CURRENT_CONTEXT = 'jarvis:visual-get-current-context',
  VISUAL_CLEAR_CONTEXT = 'jarvis:visual-clear-context',
  VISUAL_EVALUATE_GROUND_TRUTH = 'jarvis:visual-evaluate-ground-truth',

  // Phase 15 Task Orchestration IPC Channels
  TASK_CREATE = 'jarvis:task-create',
  TASK_GET = 'jarvis:task-get',
  TASK_APPROVE_STEP = 'jarvis:task-approve-step',
  TASK_EXECUTE_STEP = 'jarvis:task-execute-step',
  TASK_PAUSE = 'jarvis:task-pause',
  TASK_CANCEL = 'jarvis:task-cancel',
  TASK_RESUME = 'jarvis:task-resume',

  // Phase 16 Explainability & Human-in-the-Loop IPC Channels
  TASK_GET_EXPLANATION = 'jarvis:task-get-explanation',
  TASK_MODIFY_STEP = 'jarvis:task-modify-step',

  // Phase 17 Agent Runtime IPC Channels
  RUNTIME_GET_STATE = 'jarvis:runtime-get-state',
  RUNTIME_RECOVER = 'jarvis:runtime-recover',
  RUNTIME_GET_EVENTS = 'jarvis:runtime-get-events',

  // Phase 18 Voice IPC Channels
  VOICE_START = 'jarvis:voice-start',
  VOICE_STOP = 'jarvis:voice-stop',
  VOICE_PROCESS = 'jarvis:voice-process',
  VOICE_CONFIRM = 'jarvis:voice-confirm',
  VOICE_CANCEL = 'jarvis:voice-cancel'
}

export interface StatusChangedPayload {
  state: JarvisState;
  previousState: JarvisState;
  reason?: string;
  timestamp: number;
}

export interface ErrorNotificationPayload {
  message: string;
  code?: string;
  timestamp: number;
}

export interface JarvisConfigPayload {
  activationHotkey: string;
  emergencyHotkey: string;
  startMinimized: boolean;
  overlayMode: string;
  isDev: boolean;
}

/**
 * Global IPC Window API interface exposed to Renderer via preload contextBridge
 */
export interface JarvisElectronAPI {
  onStatusChanged: (callback: (payload: StatusChangedPayload) => void) => () => void;
  onShowOverlay: (callback: () => void) => () => void;
  onHideOverlay: (callback: () => void) => () => void;
  onErrorNotification: (callback: (payload: ErrorNotificationPayload) => void) => () => void;

  requestToggle: () => Promise<void>;
  requestEmergencyStop: () => Promise<void>;
  requestReactivate: () => Promise<void>;
  getState: () => Promise<JarvisState>;
  getConfig: () => Promise<JarvisConfigPayload>;
  requestHide: () => Promise<void>;
  requestQuit: () => Promise<void>;
  requestIgnoreMouseEvents: (ignore: boolean) => Promise<void>;

  // Phase 2 Canvas API Methods
  getCanvasState: () => Promise<unknown>;
  generateProposal: (userText?: string) => Promise<unknown>;
  acceptProposal: () => Promise<{ success: boolean; verification?: unknown; error?: string }>;
  rejectProposal: (reason?: string) => Promise<boolean>;
  modifyProposal: (ops: unknown[]) => Promise<boolean>;
  mutateCanvasManual: () => Promise<unknown>;

  // Phase 5 Version Graph API Methods
  getVersionHistory: () => Promise<unknown[]>;
  getBranches: () => Promise<unknown[]>;
  createBranch: (name: string, fromVersionId?: string) => Promise<unknown>;
  switchBranch: (branchId: string, force?: boolean) => Promise<unknown>;
  checkoutVersion: (versionId: string, force?: boolean) => Promise<unknown>;
  rollbackToVersion: (versionId: string) => Promise<unknown>;
  diffVersions: (vIdA: string, vIdB: string) => Promise<unknown>;
  commitDirty: (message?: string) => Promise<unknown>;
  discardDirty: () => Promise<unknown>;

  // Phase 6 & 7 Perception & Application Context API Methods
  perceiveDesktop: (requestCapture?: boolean) => Promise<unknown>;
  togglePerceptionPolicy: (enabled: boolean) => Promise<unknown>;
  getApplicationContext: () => Promise<unknown>;

  // Phase 8 Planning API Methods
  generatePlan: (userText: string) => Promise<unknown>;
  modifyPlan: (originalPlan: unknown, newSteps: unknown[]) => Promise<unknown>;
  acceptPlan: (plan: unknown) => Promise<unknown>;

  // Phase 9 Proposal Review API Methods
  generateProposalFromPlan: (plan: unknown) => Promise<unknown>;
  modifyProposalPhase9: (originalProposal: unknown, modifiedOps: unknown[]) => Promise<unknown>;
  acceptProposalPhase9: (proposal: unknown) => Promise<unknown>;

  // Phase 10 Controlled Execution API Method
  executeProposal: (proposal: unknown, approvalToken: unknown) => Promise<unknown>;

  // Phase 13 Visual Perception API Methods
  analyzeVisualScreen: (scenario?: string) => Promise<unknown>;
  getVisualContext: () => Promise<unknown>;
  clearVisualContext: () => Promise<unknown>;
  evaluateVisualGroundTruth: () => Promise<unknown>;

  // Phase 15 Task Orchestration API Methods
  createTask: (text: string, maxSteps?: number, maxReplans?: number) => Promise<unknown>;
  getTask: (taskId: string) => Promise<unknown>;
  approveTaskStep: (taskId: string, stepId: string) => Promise<unknown>;
  executeTaskStep: (taskId: string, stepId: string) => Promise<unknown>;
  pauseTask: (taskId: string) => Promise<unknown>;
  cancelTask: (taskId: string) => Promise<unknown>;
  resumeTask: (taskId: string) => Promise<unknown>;

  // Phase 16 Explainability & Human-in-the-Loop API Methods
  getTaskExplanation: (taskId: string, depth?: string) => Promise<unknown>;
  modifyTaskStep: (taskId: string, stepId: string, instructions: string) => Promise<unknown>;

  // Phase 17 Agent Runtime API Methods
  getRuntimeState: () => Promise<unknown>;
  recoverRuntime: (action: string, domain?: string) => Promise<unknown>;
  getRuntimeEvents: (limit?: number) => Promise<unknown>;

  // Phase 18 Voice API Methods
  startVoiceListening: () => Promise<unknown>;
  stopVoiceListening: () => Promise<unknown>;
  processVoiceSpeech: (text: string, confidence?: string) => Promise<unknown>;
  confirmVoiceTranscript: (transcriptId: string, text: string) => Promise<unknown>;
  cancelVoiceSession: () => Promise<unknown>;
}

declare global {
  interface Window {
    jarvisAPI?: JarvisElectronAPI;
  }
}
