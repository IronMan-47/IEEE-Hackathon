import { ipcMain, BrowserWindow } from 'electron';
import * as http from 'http';
import { IPCChannel, StatusChangedPayload, ErrorNotificationPayload } from '../../../core/events/ipc-contracts';
import { JarvisStateMachine } from '../../../core/state/state-machine';
import { JarvisStateEvent } from '../../../core/state/types';
import { WindowManager } from './window-manager';
import { TrayManager } from './tray-manager';
import { ConfigManager } from '../../../core/config/config-manager';
import { Logger } from '../../../core/logging/logger';
import { WorkspaceModel } from '../../../core/domain/workspace/workspace-model';
import { createCheckoutInitialScene } from '../../../core/domain/workspace/checkout-scene';
import { ProposalEngine } from '../../../core/domain/proposal/proposal-engine';
import { PatchOperationType } from '../../../core/domain/workspace/types';
import { VersionGraphManager } from '../../../core/domain/version/version-graph';

export class IPCHandler {
  private workspaceModel: WorkspaceModel;
  private versionGraphManager: VersionGraphManager;
  private proposalEngine: ProposalEngine;

  constructor(
    private stateMachine: JarvisStateMachine,
    private windowManager: WindowManager,
    private trayManager: TrayManager,
    private configManager: ConfigManager,
    private onQuitRequested: () => void
  ) {
    this.workspaceModel = new WorkspaceModel(createCheckoutInitialScene());
    this.versionGraphManager = new VersionGraphManager(undefined, () => this.stateMachine.isReady());
    this.versionGraphManager.initRootVersion('checkout_demo', this.workspaceModel.getState());
    this.proposalEngine = new ProposalEngine(
      this.workspaceModel,
      () => this.stateMachine.isReady(),
      this.versionGraphManager
    );

    this.setupListeners();
    this.setupStateObserver();
  }

  private setupListeners(): void {
    ipcMain.handle(IPCChannel.REQUEST_TOGGLE, async () => {
      this.windowManager.toggle();
    });

    ipcMain.handle(IPCChannel.REQUEST_EMERGENCY_STOP, async () => {
      Logger.warn('IPC', 'Emergency Stop requested via Renderer IPC');
      this.stateMachine.transition(JarvisStateEvent.EMERGENCY_STOP, 'Requested via UI Renderer');
      
      try {
        await this.callPythonAgentGeneric('/api/runtime/stop', {});
      } catch (err: unknown) {
        Logger.error('IPC', `Failed to propagate emergency stop to Python backend: ${String(err)}`);
      }
      
      this.windowManager.hide();
    });

    ipcMain.handle(IPCChannel.REQUEST_REACTIVATE, async () => {
      Logger.info('IPC', 'Reactivate requested via Renderer IPC');
      this.stateMachine.transition(JarvisStateEvent.RESET_TO_READY, 'Reactivated via UI Renderer');
      
      try {
        await this.callPythonAgentGeneric('/api/runtime/resume', {});
      } catch (err: unknown) {
        Logger.error('IPC', `Failed to propagate resume to Python backend: ${String(err)}`);
      }
    });

    ipcMain.handle(IPCChannel.REQUEST_GET_STATE, async () => {
      return this.stateMachine.getState();
    });

    ipcMain.handle(IPCChannel.REQUEST_GET_CONFIG, async () => {
      return this.configManager.getConfig();
    });

    ipcMain.handle(IPCChannel.REQUEST_HIDE, async () => {
      this.windowManager.hide();
    });

    ipcMain.handle(IPCChannel.REQUEST_QUIT, async () => {
      this.onQuitRequested();
    });

    ipcMain.handle(IPCChannel.REQUEST_IGNORE_MOUSE_EVENTS, async (_event, ignore: boolean) => {
      const win = this.windowManager.getWindow();
      if (win) {
        if (ignore) {
          win.setIgnoreMouseEvents(true, { forward: true });
        } else {
          win.setIgnoreMouseEvents(false);
        }
      }
    });

    // Phase 2 Canvas Handlers
    ipcMain.handle(IPCChannel.CANVAS_GET_STATE, async () => {
      return this.workspaceModel.getState();
    });

    ipcMain.handle(IPCChannel.CANVAS_GENERATE_PROPOSAL, async (_event, userText?: string) => {
      const promptText = userText || 'Make the Pay Now button more prominent';
      const currentWorkspace = this.workspaceModel.getState();

      const payload = {
        request_id: `req_${Date.now()}`,
        text: promptText,
        workspace_context: currentWorkspace
      };

      try {
        const responseData = await this.callPythonAgent(payload);
        if (responseData && responseData.status === 'SUCCESS' && responseData.proposal) {
          Logger.info('IPC', `Python Agent Core returned AI proposal [ ${responseData.proposal.title} ]`);
          return responseData.proposal;
        } else if (responseData && responseData.error) {
          Logger.warn('IPC', `Python Agent Core error: ${responseData.error}`);
          return this.proposalEngine.generateCheckoutCtaProposal();
        }
      } catch (err: unknown) {
        Logger.warn('IPC', `Python Agent Core HTTP call failed: ${String(err)}. Falling back to local proposal engine.`);
      }

      const prop = this.proposalEngine.generateCheckoutCtaProposal();
      Logger.info('IPC', `Generated fallback proposal [ ${prop.title} ] against Revision ${prop.baseRevision}`);
      return prop;
    });

    ipcMain.handle(IPCChannel.CANVAS_ACCEPT_PROPOSAL, async () => {
      const res = this.proposalEngine.acceptAndExecuteProposal();
      Logger.info('IPC', `Executed proposal -> Success: ${res.success}, Verified: ${res.verification?.verified}`);
      return res;
    });

    ipcMain.handle(IPCChannel.CANVAS_REJECT_PROPOSAL, async (_event, reason?: string) => {
      const ok = this.proposalEngine.rejectProposal(reason);
      Logger.info('IPC', `Rejected proposal -> ${ok}`);
      return ok;
    });

    ipcMain.handle(IPCChannel.CANVAS_MODIFY_PROPOSAL, async (_event, ops: any) => {
      const ok = this.proposalEngine.modifyProposal(ops);
      Logger.info('IPC', `Modified proposal -> ${ok}`);
      return ok;
    });

    ipcMain.handle(IPCChannel.CANVAS_MUTATE_MANUAL, async () => {
      const op = {
        op: PatchOperationType.MOVE_ELEMENT,
        targetId: 'card_summary',
        proposedValue: { x: 40, y: 90 },
        reason: 'Simulated manual drag edit'
      };
      this.workspaceModel.applyPatch([op]);
      this.versionGraphManager.markDirty([op]);
      Logger.warn('IPC', `Simulated manual edit applied -> Workspace Revision is now ${this.workspaceModel.getRevision()} (DIRTY)`);
      return this.workspaceModel.getState();
    });

    // Phase 5 Version Graph IPC Handlers
    ipcMain.handle(IPCChannel.VERSION_GET_HISTORY, async () => {
      return this.versionGraphManager.getHistory();
    });

    ipcMain.handle(IPCChannel.VERSION_GET_BRANCHES, async () => {
      return this.versionGraphManager.getAllBranches();
    });

    ipcMain.handle(IPCChannel.VERSION_CREATE_BRANCH, async (_event, name: string, fromVersionId?: string) => {
      const branch = this.versionGraphManager.createBranch(name, fromVersionId);
      Logger.info('IPC', `Created branch [ ${branch.name} ] at version ${branch.headVersionId}`);
      return branch;
    });

    ipcMain.handle(IPCChannel.VERSION_SWITCH_BRANCH, async (_event, branchId: string, force?: boolean) => {
      const reconstructedState = this.versionGraphManager.checkoutBranch(branchId, { force });
      this.workspaceModel = new WorkspaceModel(reconstructedState);
      Logger.info('IPC', `Switched active branch to [ ${branchId} ] -> Revision ${reconstructedState.revision}`);
      return reconstructedState;
    });

    ipcMain.handle(IPCChannel.VERSION_CHECKOUT, async (_event, versionId: string, force?: boolean) => {
      const reconstructedState = this.versionGraphManager.checkoutVersion(versionId, { force });
      this.workspaceModel = new WorkspaceModel(reconstructedState);
      Logger.info('IPC', `Checked out version [ ${versionId} ] -> Revision ${reconstructedState.revision}`);
      return reconstructedState;
    });

    ipcMain.handle(IPCChannel.VERSION_ROLLBACK, async (_event, versionId: string) => {
      const res = this.versionGraphManager.rollbackToVersion(versionId);
      this.workspaceModel = new WorkspaceModel(res.state);
      Logger.info('IPC', `Rolled back state to version [ ${versionId} ] -> Created version ${res.newVersion.id}`);
      return res;
    });

    ipcMain.handle(IPCChannel.VERSION_DIFF, async (_event, vA: string, vB: string) => {
      return this.versionGraphManager.diffVersions(vA, vB);
    });

    ipcMain.handle(IPCChannel.VERSION_COMMIT_DIRTY, async (_event, message?: string) => {
      const msg = message || 'User manual workspace edits';
      const version = this.versionGraphManager.commitDirty('checkout_demo', this.workspaceModel.getState(), msg);
      Logger.info('IPC', `Committed dirty state -> Created version ${version.id}`);
      return version;
    });

    ipcMain.handle(IPCChannel.VERSION_DISCARD_DIRTY, async () => {
      const restoredState = this.versionGraphManager.discardDirty();
      this.workspaceModel = new WorkspaceModel(restoredState);
      Logger.info('IPC', `Discarded dirty state -> Restored head state (Rev ${restoredState.revision})`);
      return restoredState;
    });

    // Phase 6 & 7 Perception & Application Context IPC Handlers
    ipcMain.handle(IPCChannel.PERCEIVE_DESKTOP, async (_event, requestCapture: boolean = true) => {
      try {
        const payload = {
          request_capture: requestCapture,
          workspace_context: this.workspaceModel.getState()
        };
        const responseData = await this.callPythonAgentGeneric('/agent/perceive', payload);
        Logger.info('IPC', `Desktop Perception: Active App [ ${responseData.active_application?.name} ], Classification: ${responseData.classification}, Adapter: ${responseData.application_context?.application}`);
        return responseData;
      } catch (err: unknown) {
        Logger.warn('IPC', `Perception call failed: ${String(err)}`);
        return {
          timestamp: Date.now(),
          active_application: { name: 'Unknown Application', process_name: 'unknown.exe' },
          active_window: { title: 'Unknown Desktop Window', width: 1920, height: 1080 },
          screen_metadata: { primary_width: 1920, primary_height: 1080 },
          capture_metadata: { captured: false },
          classification: 'UNKNOWN',
          perception_enabled: false,
          application_context: {
            application: 'unknown',
            status: 'UNSUPPORTED',
            confidence: 'UNAVAILABLE',
            privacy: 'PUBLIC',
            capabilities: [],
            data: { reason: 'Perception IPC failure fallback' }
          }
        };
      }
    });

    ipcMain.handle(IPCChannel.PERCEIVE_POLICY_TOGGLE, async (_event, enabled: boolean) => {
      try {
        const responseData = await this.callPythonAgentGeneric('/agent/perceive/policy', { enabled });
        Logger.info('IPC', `Perception Policy Toggled -> Enabled: ${enabled}`);
        return responseData;
      } catch (err: unknown) {
        Logger.warn('IPC', `Perception policy toggle failed: ${String(err)}`);
        return { status: 'error', error: String(err) };
      }
    });

    ipcMain.handle(IPCChannel.PERCEIVE_GET_APP_CONTEXT, async () => {
      try {
        const responseData = await this.callPythonAgentGeneric('/agent/perceive', {
          request_capture: false,
          workspace_context: this.workspaceModel.getState()
        });
        return responseData.application_context || null;
      } catch (err: unknown) {
        Logger.warn('IPC', `Get application context failed: ${String(err)}`);
        return null;
      }
    });

    // Phase 8 Planning Pipeline IPC Handlers
    ipcMain.handle(IPCChannel.PLAN_GENERATE, async (_event, userText: string) => {
      try {
        const perceptionData = await this.callPythonAgentGeneric('/agent/perceive', {
          request_capture: false,
          workspace_context: this.workspaceModel.getState()
        });

        const planPayload = {
          text: userText,
          perception_context: perceptionData,
          workspace_context: this.workspaceModel.getState()
        };

        const planResponse = await this.callPythonAgentGeneric('/agent/plan', planPayload);
        Logger.info('IPC', `Generated Plan -> Status: ${planResponse.status}`);
        return planResponse;
      } catch (err: unknown) {
        Logger.warn('IPC', `Plan generation failed: ${String(err)}`);
        return { status: 'ERROR', error: String(err) };
      }
    });

    ipcMain.handle(IPCChannel.PLAN_MODIFY, async (_event, originalPlan: unknown, newSteps: unknown[]) => {
      try {
        const responseData = await this.callPythonAgentGeneric('/agent/plan/modify', {
          original_plan: originalPlan,
          new_steps: newSteps
        });
        Logger.info('IPC', `Modified Plan -> Status: ${responseData.status}`);
        return responseData;
      } catch (err: unknown) {
        Logger.warn('IPC', `Plan modification failed: ${String(err)}`);
        return { status: 'ERROR', error: String(err) };
      }
    });

    ipcMain.handle(IPCChannel.PLAN_ACCEPT, async (_event, plan: unknown) => {
      try {
        const responseData = await this.callPythonAgentGeneric('/agent/plan/accept', { plan });
        Logger.info('IPC', `Accepted Plan -> Status: ${responseData.status}`);
        return responseData;
      } catch (err: unknown) {
        Logger.warn('IPC', `Plan acceptance failed: ${String(err)}`);
        return { status: 'ERROR', error: String(err) };
      }
    });

    // Phase 9 Proposal Review IPC Handlers
    ipcMain.handle(IPCChannel.PROPOSAL_GENERATE_FROM_PLAN, async (_event, plan: unknown) => {
      try {
        const perceptionData = await this.callPythonAgentGeneric('/agent/perceive', {
          request_capture: false,
          workspace_context: this.workspaceModel.getState()
        });

        const proposalPayload = {
          plan: plan,
          perception_context: perceptionData,
          workspace_context: this.workspaceModel.getState()
        };

        const responseData = await this.callPythonAgentGeneric('/agent/propose/from-plan', proposalPayload);
        Logger.info('IPC', `Generated Proposal from Plan -> Status: ${responseData.status}`);
        return responseData;
      } catch (err: unknown) {
        Logger.warn('IPC', `Proposal generation from plan failed: ${String(err)}`);
        return { status: 'ERROR', error: String(err) };
      }
    });

    ipcMain.handle(IPCChannel.PROPOSAL_MODIFY_PHASE9, async (_event, originalProposal: unknown, modifiedOps: unknown[]) => {
      try {
        const perceptionData = await this.callPythonAgentGeneric('/agent/perceive', {
          request_capture: false,
          workspace_context: this.workspaceModel.getState()
        });

        const responseData = await this.callPythonAgentGeneric('/agent/propose/modify', {
          original_proposal: originalProposal,
          modified_operations: modifiedOps,
          perception_context: perceptionData,
          workspace_context: this.workspaceModel.getState()
        });
        Logger.info('IPC', `Modified Proposal Phase 9 -> Status: ${responseData.status}`);
        return responseData;
      } catch (err: unknown) {
        Logger.warn('IPC', `Proposal modification Phase 9 failed: ${String(err)}`);
        return { status: 'ERROR', error: String(err) };
      }
    });

    ipcMain.handle(IPCChannel.PROPOSAL_ACCEPT_PHASE9, async (_event, proposal: unknown) => {
      try {
        const perceptionData = await this.callPythonAgentGeneric('/agent/perceive', {
          request_capture: false,
          workspace_context: this.workspaceModel.getState()
        });

        const responseData = await this.callPythonAgentGeneric('/agent/propose/accept', {
          proposal: proposal,
          perception_context: perceptionData,
          workspace_context: this.workspaceModel.getState()
        });
        Logger.info('IPC', `Accepted Proposal Phase 9 -> Token: ${responseData.approval_token?.tokenId}. NO EXECUTION.`);
        return responseData;
      } catch (err: unknown) {
        Logger.warn('IPC', `Proposal acceptance Phase 9 failed: ${String(err)}`);
        return { status: 'ERROR', error: String(err) };
      }
    });

    // Phase 10 Controlled Execution IPC Handler
    ipcMain.handle(IPCChannel.EXECUTE_PROPOSAL, async (_event, proposal: any, approvalToken: any) => {
      try {
        const perceptionData = await this.callPythonAgentGeneric('/agent/perceive', {
          request_capture: false,
          workspace_context: this.workspaceModel.getState()
        });

        const executionRequest = {
          proposal_id: proposal.proposal_id,
          approval_token: approvalToken,
          workspace_id: 'checkout_demo',
          base_revision: proposal.base_revision,
          base_context_id: proposal.base_context_id || 'living_canvas_ctx',
          base_context_hash: proposal.base_context_hash || ''
        };

        const responseData = await this.callPythonAgentGeneric('/agent/execute', {
          execution_request: executionRequest,
          proposal: proposal,
          perception_context: perceptionData,
          workspace_context: this.workspaceModel.getState()
        });

        Logger.info('IPC', `Executed Proposal Phase 10 -> Status: ${responseData.status}`);

        if (responseData.status === 'COMMITTED' && responseData.execution_result) {
          const res = responseData.execution_result;
          if (res.operations_applied && res.operations_applied.length > 0) {
            // Apply operations to sync Electron main workspace model
            const patchOps = res.operations_applied.map((op: any) => ({
              op: op.op_type,
              targetId: op.target,
              proposedValue: op.parameters,
              reason: op.reason
            }));
            this.workspaceModel.applyPatch(patchOps);
            this.versionGraphManager.markDirty([]); // sync revision
          }
        }

        return responseData;
      } catch (err: unknown) {
        Logger.warn('IPC', `Proposal execution Phase 10 failed: ${String(err)}`);
        return { status: 'FAILED', error: String(err) };
      }
    });

    // Phase 13 Visual Perception IPC Handlers
    ipcMain.handle(IPCChannel.VISUAL_ANALYZE_SCREEN, async (_event, scenario?: string) => {
      try {
        const payload = { scenario, request_capture: true, workspace_context: this.workspaceModel.getState() };
        const res = await this.callPythonAgentGeneric('/agent/visual/analyze', payload);
        return res;
      } catch (err: unknown) {
        Logger.warn('IPC', `Visual perception analyze failed: ${String(err)}`);
        return { status: 'FAILED', error: String(err) };
      }
    });

    ipcMain.handle(IPCChannel.VISUAL_GET_CURRENT_CONTEXT, async () => {
      try {
        const res = await this.callPythonAgentGeneric('/agent/visual/current', {});
        return res;
      } catch (err: unknown) {
        return { status: 'FAILED', error: String(err) };
      }
    });

    ipcMain.handle(IPCChannel.VISUAL_CLEAR_CONTEXT, async () => {
      try {
        const res = await this.callPythonAgentGeneric('/agent/visual/clear', {});
        return res;
      } catch (err: unknown) {
        return { status: 'FAILED', error: String(err) };
      }
    });

    ipcMain.handle(IPCChannel.VISUAL_EVALUATE_GROUND_TRUTH, async () => {
      try {
        const currentElements = Object.values(this.workspaceModel.getState().elements || {}).map((e: any) => ({
          id: e.id,
          text: e.props?.text || e.name || '',
          x: e.bounds?.x || 0,
          y: e.bounds?.y || 0,
          width: e.bounds?.width || 100,
          height: e.bounds?.height || 30
        }));
        const res = await this.callPythonAgentGeneric('/agent/visual/ground_truth', { actual_elements: currentElements });
        return res;
      } catch (err: unknown) {
        Logger.warn('IPC', `Visual ground-truth eval failed: ${String(err)}`);
        return { status: 'FAILED', error: String(err) };
      }
    });

    // Phase 15 Task Orchestration Handlers
    ipcMain.handle(IPCChannel.TASK_CREATE, async (_event, text: string, maxSteps?: number, maxReplans?: number) => {
      try {
        const workspaceContext = this.workspaceModel.getState();
        return await this.callPythonAgentGeneric('/agent/tasks/create', {
          text,
          workspace_context: workspaceContext,
          max_steps: maxSteps ?? 10,
          max_replans: maxReplans ?? 3
        });
      } catch (err: unknown) {
        Logger.warn('IPC', `Task create failed: ${String(err)}`);
        return { status: 'FAILED', error: String(err) };
      }
    });

    ipcMain.handle(IPCChannel.TASK_GET, async (_event, taskId: string) => {
      try {
        return await this.callPythonAgentGet(`/agent/tasks/${taskId}`);
      } catch (err: unknown) {
        Logger.warn('IPC', `Task get failed: ${String(err)}`);
        return { status: 'FAILED', error: String(err) };
      }
    });

    ipcMain.handle(IPCChannel.TASK_APPROVE_STEP, async (_event, taskId: string, stepId: string) => {
      try {
        const workspaceContext = this.workspaceModel.getState();
        return await this.callPythonAgentGeneric('/agent/tasks/step/approve', {
          task_id: taskId,
          step_id: stepId,
          workspace_context: workspaceContext
        });
      } catch (err: unknown) {
        Logger.warn('IPC', `Task step approve failed: ${String(err)}`);
        return { status: 'FAILED', error: String(err) };
      }
    });

    ipcMain.handle(IPCChannel.TASK_EXECUTE_STEP, async (_event, taskId: string, stepId: string) => {
      try {
        const workspaceContext = this.workspaceModel.getState();
        return await this.callPythonAgentGeneric('/agent/tasks/step/execute', {
          task_id: taskId,
          step_id: stepId,
          workspace_context: workspaceContext
        });
      } catch (err: unknown) {
        Logger.warn('IPC', `Task step execute failed: ${String(err)}`);
        return { status: 'FAILED', error: String(err) };
      }
    });

    ipcMain.handle(IPCChannel.TASK_PAUSE, async (_event, taskId: string) => {
      try {
        return await this.callPythonAgentGeneric('/agent/tasks/pause', { task_id: taskId });
      } catch (err: unknown) {
        Logger.warn('IPC', `Task pause failed: ${String(err)}`);
        return { status: 'FAILED', error: String(err) };
      }
    });

    ipcMain.handle(IPCChannel.TASK_CANCEL, async (_event, taskId: string) => {
      try {
        return await this.callPythonAgentGeneric('/agent/tasks/cancel', { task_id: taskId });
      } catch (err: unknown) {
        Logger.warn('IPC', `Task cancel failed: ${String(err)}`);
        return { status: 'FAILED', error: String(err) };
      }
    });

    ipcMain.handle(IPCChannel.TASK_RESUME, async (_event, taskId: string) => {
      try {
        return await this.callPythonAgentGeneric('/agent/tasks/resume', { task_id: taskId });
      } catch (err: unknown) {
        Logger.warn('IPC', `Task resume failed: ${String(err)}`);
        return { status: 'FAILED', error: String(err) };
      }
    });

    // Phase 16 Explainability & Human-in-the-Loop Handlers
    ipcMain.handle(IPCChannel.TASK_GET_EXPLANATION, async (_event, taskId: string, depth?: string) => {
      try {
        const queryParams = depth ? `?depth=${encodeURIComponent(depth)}` : '';
        return await this.callPythonAgentGet(`/agent/tasks/${taskId}/explanation${queryParams}`);
      } catch (err: unknown) {
        Logger.warn('IPC', `Task get explanation failed: ${String(err)}`);
        return { status: 'FAILED', error: String(err) };
      }
    });

    ipcMain.handle(IPCChannel.TASK_MODIFY_STEP, async (_event, taskId: string, stepId: string, instructions: string) => {
      try {
        const workspaceContext = this.workspaceModel.getState();
        return await this.callPythonAgentGeneric('/agent/tasks/step/modify', {
          task_id: taskId,
          step_id: stepId,
          modification_instructions: instructions,
          workspace_context: workspaceContext
        });
      } catch (err: unknown) {
        Logger.warn('IPC', `Task modify step failed: ${String(err)}`);
        return { status: 'FAILED', error: String(err) };
      }
    });

    // Phase 17 Agent Runtime Handlers
    ipcMain.handle(IPCChannel.RUNTIME_GET_STATE, async () => {
      try {
        return await this.callPythonAgentGet('/agent/runtime/state');
      } catch (err: unknown) {
        return { status: 'FAILED', error: String(err) };
      }
    });

    ipcMain.handle(IPCChannel.RUNTIME_RECOVER, async (_event, action: string, domain?: string) => {
      try {
        const workspaceContext = this.workspaceModel.getState();
        return await this.callPythonAgentGeneric('/agent/runtime/recover', {
          action,
          domain,
          workspace_context: workspaceContext
        });
      } catch (err: unknown) {
        return { status: 'FAILED', error: String(err) };
      }
    });

    ipcMain.handle(IPCChannel.RUNTIME_GET_EVENTS, async (_event, limit?: number) => {
      try {
        const queryParams = limit ? `?limit=${limit}` : '';
        return await this.callPythonAgentGet(`/agent/runtime/events${queryParams}`);
      } catch (err: unknown) {
        return { status: 'FAILED', error: String(err) };
      }
    });

    // Phase 18 Voice Handlers
    ipcMain.handle(IPCChannel.VOICE_START, async () => {
      try {
        return await this.callPythonAgentGeneric('/agent/voice/start', {});
      } catch (err: unknown) {
        return { status: 'FAILED', error: String(err) };
      }
    });

    ipcMain.handle(IPCChannel.VOICE_STOP, async () => {
      try {
        return await this.callPythonAgentGeneric('/agent/voice/stop', {});
      } catch (err: unknown) {
        return { status: 'FAILED', error: String(err) };
      }
    });

    ipcMain.handle(IPCChannel.VOICE_PROCESS, async (_event, text: string, confidence?: string) => {
      try {
        return await this.callPythonAgentGeneric('/agent/voice/process', { text, confidence: confidence || 'HIGH' });
      } catch (err: unknown) {
        return { status: 'FAILED', error: String(err) };
      }
    });

    ipcMain.handle(IPCChannel.VOICE_CONFIRM, async (_event, transcriptId: string, text: string) => {
      try {
        return await this.callPythonAgentGeneric('/agent/voice/confirm', { transcript_id: transcriptId, text });
      } catch (err: unknown) {
        return { status: 'FAILED', error: String(err) };
      }
    });

    ipcMain.handle(IPCChannel.VOICE_CANCEL, async () => {
      try {
        return await this.callPythonAgentGeneric('/agent/voice/cancel', {});
      } catch (err: unknown) {
        return { status: 'FAILED', error: String(err) };
      }
    });
  }

  private setupStateObserver(): void {
    this.stateMachine.subscribe((event) => {
      const payload: StatusChangedPayload = {
        state: event.toState,
        previousState: event.fromState,
        reason: event.reason,
        timestamp: event.timestamp
      };

      this.broadcast(IPCChannel.STATUS_CHANGED, payload);
      this.trayManager.updateContextMenu();
    });
  }

  public notifyError(message: string, code?: string): void {
    const payload: ErrorNotificationPayload = {
      message,
      code,
      timestamp: Date.now()
    };
    this.broadcast(IPCChannel.ERROR_NOTIFICATION, payload);
  }

  private broadcast(channel: string, payload: unknown): void {
    const win = this.windowManager.getWindow();
    if (win && !win.isDestroyed()) {
      win.webContents.send(channel, payload);
    }
  }

  private callPythonAgentGeneric(pathStr: string, payload: any): Promise<any> {
    return new Promise((resolve, reject) => {
      const postData = JSON.stringify(payload);
      const req = http.request({
        hostname: '127.0.0.1',
        port: 8765,
        path: pathStr,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(postData)
        }
      }, (res) => {
        let body = '';
        res.on('data', chunk => body += chunk);
        res.on('end', () => {
          try {
            resolve(JSON.parse(body));
          } catch (e) {
            reject(e);
          }
        });
      });

      req.on('error', (err) => reject(err));
      req.setTimeout(4000, () => {
        req.destroy();
        reject(new Error(`Python Agent request to ${pathStr} timed out`));
      });

      req.write(postData);
      req.end();
    });
  }

  private callPythonAgentGet(pathStr: string): Promise<any> {
    return new Promise((resolve, reject) => {
      const req = http.request({
        hostname: '127.0.0.1',
        port: 8765,
        path: pathStr,
        method: 'GET'
      }, (res) => {
        let body = '';
        res.on('data', chunk => body += chunk);
        res.on('end', () => {
          try {
            resolve(JSON.parse(body));
          } catch (e) {
            reject(e);
          }
        });
      });

      req.on('error', (err) => reject(err));
      req.setTimeout(4000, () => {
        req.destroy();
        reject(new Error(`Python Agent GET request to ${pathStr} timed out`));
      });

      req.end();
    });
  }

  private callPythonAgent(payload: any): Promise<any> {
    return this.callPythonAgentGeneric('/agent/propose', payload);
  }

  public destroy(): void {
    ipcMain.removeHandler(IPCChannel.REQUEST_TOGGLE);
    ipcMain.removeHandler(IPCChannel.REQUEST_EMERGENCY_STOP);
    ipcMain.removeHandler(IPCChannel.REQUEST_REACTIVATE);
    ipcMain.removeHandler(IPCChannel.REQUEST_GET_STATE);
    ipcMain.removeHandler(IPCChannel.REQUEST_GET_CONFIG);
    ipcMain.removeHandler(IPCChannel.REQUEST_HIDE);
    ipcMain.removeHandler(IPCChannel.REQUEST_QUIT);
  }
}
