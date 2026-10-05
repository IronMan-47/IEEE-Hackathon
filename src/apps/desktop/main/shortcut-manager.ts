import { globalShortcut } from 'electron';
import * as http from 'node:http';
import { WindowManager } from './window-manager';
import { TrayManager } from './tray-manager';
import { JarvisStateMachine } from '../../../core/state/state-machine';
import { JarvisState, JarvisStateEvent } from '../../../core/state/types';
import { Logger } from '../../../core/logging/logger';

export class ShortcutManager {
  constructor(
    private windowManager: WindowManager,
    private trayManager: TrayManager,
    private stateMachine: JarvisStateMachine,
    private activationHotkey: string = 'Ctrl+Shift+Space',
    private emergencyHotkey: string = 'Ctrl+Shift+Escape'
  ) {}

  public registerShortcuts(): void {
    this.unregisterAll();

    // 1. Global Activation Shortcut
    try {
      const retActivation = globalShortcut.register(this.activationHotkey, () => {
        this.handleActivationShortcut();
      });

      if (!retActivation) {
        Logger.error('HOTKEY', `Failed to register activation shortcut: ${this.activationHotkey}`);
      } else {
        Logger.info('HOTKEY', `Registered activation shortcut: ${this.activationHotkey}`);
      }
    } catch (err: unknown) {
      Logger.error('HOTKEY', `Exception registering activation shortcut`, { error: String(err) });
    }

    // 2. Emergency Stop Shortcut
    try {
      const retEmergency = globalShortcut.register(this.emergencyHotkey, () => {
        this.handleEmergencyShortcut();
      });

      if (!retEmergency) {
        Logger.error('HOTKEY', `Failed to register emergency shortcut: ${this.emergencyHotkey}`);
      } else {
        Logger.info('HOTKEY', `Registered emergency shortcut: ${this.emergencyHotkey}`);
      }
    } catch (err: unknown) {
      Logger.error('HOTKEY', `Exception registering emergency shortcut`, { error: String(err) });
    }
  }

  private handleActivationShortcut(): void {
    const currentState = this.stateMachine.getState();

    // Guard: Emergency Stop block
    if (currentState === JarvisState.STOPPED) {
      Logger.warn('HOTKEY', 'Global activation suppressed: System is in STOPPED state');
      return;
    }

    // Guard: User tray activation toggle
    if (!this.trayManager.isActivationAllowed()) {
      Logger.warn('HOTKEY', 'Global activation suppressed: Disabled via tray menu');
      return;
    }

    if (this.windowManager.isVisible()) {
      this.windowManager.hide();
      if (currentState === JarvisState.ACTIVE) {
        this.stateMachine.transition(JarvisStateEvent.DEACTIVATE, 'Hidden via hotkey');
      }
    } else {
      this.windowManager.show();
      if (currentState === JarvisState.READY) {
        this.stateMachine.transition(JarvisStateEvent.ACTIVATE, 'Shown via hotkey');
      }
    }
  }

  private handleEmergencyShortcut(): void {
    Logger.warn('HOTKEY', 'EMERGENCY STOP shortcut triggered!');
    this.stateMachine.transition(JarvisStateEvent.EMERGENCY_STOP, 'Triggered via global shortcut Ctrl+Shift+Escape');
    this.windowManager.hide();
    
    // Propagate to Python backend
    const req = http.request({
      hostname: '127.0.0.1',
      port: 8765,
      path: '/api/runtime/stop',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    }, (res) => {
      Logger.info('HOTKEY', `Emergency stop propagated to backend. Status: ${res.statusCode}`);
    });
    req.on('error', (e) => {
      Logger.error('HOTKEY', `Failed to propagate emergency stop to backend: ${e.message}`);
    });
    req.write('{}');
    req.end();
  }

  public unregisterAll(): void {
    globalShortcut.unregisterAll();
    Logger.info('HOTKEY', 'Unregistered all global shortcuts');
  }
}
