import { app } from 'electron';
import * as path from 'path';
import { ConfigManager } from '../../../core/config/config-manager';
import { JarvisStateMachine } from '../../../core/state/state-machine';
import { JarvisStateEvent } from '../../../core/state/types';
import { Logger } from '../../../core/logging/logger';
import { WindowManager } from './window-manager';
import { TrayManager } from './tray-manager';
import { ShortcutManager } from './shortcut-manager';
import { IPCHandler } from './ipc-handler';
import { PythonProcessManager } from './python-process-manager';

class JarvisDesktopApp {
  private configManager: ConfigManager;
  private stateMachine: JarvisStateMachine;
  private windowManager: WindowManager;
  private pythonProcessManager: PythonProcessManager;
  private trayManager: TrayManager | null = null;
  private shortcutManager: ShortcutManager | null = null;
  private ipcHandler: IPCHandler | null = null;

  constructor() {
    this.configManager = new ConfigManager();
    this.stateMachine = new JarvisStateMachine();
    this.windowManager = new WindowManager();
    this.pythonProcessManager = new PythonProcessManager();
  }

  public async start(): Promise<void> {
    Logger.info('SHELL', '==================================================');
    Logger.info('SHELL', 'JARVIS — The Living Canvas Desktop Agent (Phase 1)');
    Logger.info('SHELL', '==================================================');

    // Single instance lock
    const gotLock = app.requestSingleInstanceLock();
    if (!gotLock) {
      Logger.warn('SHELL', 'Another instance of JARVIS is already running. Exiting.');
      app.quit();
      return;
    }

    app.on('second-instance', () => {
      Logger.info('SHELL', 'Second instance launched -> Bringing primary instance window to focus');
      this.windowManager.show();
    });

    await app.whenReady();

    this.bootstrap();
  }

  private bootstrap(): void {
    const preloadPath = path.join(__dirname, 'preload.js');

    // 1. Initialize Window Manager
    this.windowManager.createWindow(preloadPath);

    // 2. Start Python Agent Core Daemon Process
    this.pythonProcessManager.startDaemon();

    // 3. Initialize Tray Manager
    this.trayManager = new TrayManager(
      this.windowManager,
      this.stateMachine,
      () => this.quitApp()
    );
    this.trayManager.initTray();

    // 3. Initialize Shortcut Manager
    const config = this.configManager.getConfig();
    this.shortcutManager = new ShortcutManager(
      this.windowManager,
      this.trayManager,
      this.stateMachine,
      config.activationHotkey,
      config.emergencyHotkey
    );
    this.shortcutManager.registerShortcuts();

    // 4. Initialize IPC Handler
    this.ipcHandler = new IPCHandler(
      this.stateMachine,
      this.windowManager,
      this.trayManager,
      this.configManager,
      () => this.quitApp()
    );

    // 5. Initialize State Machine -> READY
    const ok = this.stateMachine.transition(JarvisStateEvent.INITIALIZE, 'Desktop App Initialized');
    if (ok) {
      Logger.info('STATE', `JARVIS State Machine initialized to [ ${this.stateMachine.getState()} ]`);
    } else {
      Logger.error('STATE', 'Failed to transition State Machine to READY');
    }

    app.on('will-quit', () => {
      this.cleanup();
    });

    app.on('window-all-closed', () => {
      // Keep process running in tray on Windows even when window closes
      if (process.platform !== 'darwin') {
        Logger.info('SHELL', 'All windows closed; keeping JARVIS running in background tray');
      }
    });

    Logger.info('SHELL', 'JARVIS Phase 1 Desktop Application started successfully');
  }

  private quitApp(): void {
    Logger.info('SHELL', 'Quit requested by user -> Terminating JARVIS process cleanly');
    this.windowManager.prepareQuit();
    this.cleanup();
    app.quit();
  }

  private cleanup(): void {
    if (this.pythonProcessManager) {
      this.pythonProcessManager.stopDaemon();
    }
    if (this.shortcutManager) {
      this.shortcutManager.unregisterAll();
    }
    if (this.trayManager) {
      this.trayManager.destroy();
    }
    if (this.ipcHandler) {
      this.ipcHandler.destroy();
    }
  }
}

const jarvisApp = new JarvisDesktopApp();
jarvisApp.start().catch((err) => {
  Logger.error('SHELL', 'Fatal error starting JARVIS desktop application', { error: String(err) });
});
