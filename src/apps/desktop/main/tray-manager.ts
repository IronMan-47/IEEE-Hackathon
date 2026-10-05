import { Tray, Menu, nativeImage, MenuItemConstructorOptions } from 'electron';
import { WindowManager } from './window-manager';
import { JarvisStateMachine } from '../../../core/state/state-machine';
import { JarvisState, JarvisStateEvent } from '../../../core/state/types';
import { Logger } from '../../../core/logging/logger';

/**
 * 16x16 PNG Base64 Icon representing JARVIS Core (cyan emblem on dark circle)
 */
const TRAY_ICON_BASE64 = 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAA6SURBVDhPY2AYBaNgFCAG/gNiwgB0zQxQgB8T1gB8+BkgG6Dx9f//f0yg4wAEgPz35y9f4cMFAAA+Zhsx57rNqwAAAABJRU5ErkJggg==';

export class TrayManager {
  private tray: Tray | null = null;
  private isActivationEnabled: boolean = true;

  constructor(
    private windowManager: WindowManager,
    private stateMachine: JarvisStateMachine,
    private onQuit: () => void
  ) {}

  public initTray(): void {
    try {
      const icon = nativeImage.createFromDataURL(`data:image/png;base64,${TRAY_ICON_BASE64}`);
      this.tray = new Tray(icon);
      this.tray.setToolTip('JARVIS — Living Canvas (Ready)');

      this.tray.on('click', () => {
        this.windowManager.toggle();
      });

      this.updateContextMenu();
      Logger.info('TRAY', 'System tray initialized successfully');
    } catch (err: unknown) {
      Logger.error('TRAY', 'Failed to initialize system tray', { error: String(err) });
    }
  }

  public isActivationAllowed(): boolean {
    return this.isActivationEnabled;
  }

  public updateContextMenu(): void {
    if (!this.tray) return;

    const currentState = this.stateMachine.getState();
    const isStopped = currentState === JarvisState.STOPPED;
    const isVisible = this.windowManager.isVisible();

    const menuTemplate: MenuItemConstructorOptions[] = [
      {
        label: `JARVIS State: [ ${currentState} ]`,
        enabled: false
      },
      { type: 'separator' },
      {
        label: isVisible ? 'Hide JARVIS' : 'Open JARVIS',
        click: () => {
          if (isStopped) {
            Logger.warn('TRAY', 'Cannot open window while in STOPPED state. Please reset to READY.');
            return;
          }
          this.windowManager.toggle();
        }
      },
      {
        label: 'Global Activation Shortcut',
        type: 'checkbox',
        checked: this.isActivationEnabled,
        click: (menuItem) => {
          this.isActivationEnabled = menuItem.checked;
          Logger.info('TRAY', `Global activation toggle changed: ${this.isActivationEnabled}`);
        }
      },
      { type: 'separator' },
      {
        label: '🛑 Emergency Stop',
        enabled: !isStopped,
        click: () => {
          this.stateMachine.transition(JarvisStateEvent.EMERGENCY_STOP, 'Triggered via System Tray');
          this.windowManager.hide();
          Logger.warn('TRAY', 'Emergency Stop activated via System Tray');
          this.updateContextMenu();
        }
      },
      {
        label: '🔄 Reset to READY',
        enabled: isStopped,
        click: () => {
          this.stateMachine.transition(JarvisStateEvent.RESET_TO_READY, 'Reset via System Tray');
          Logger.info('TRAY', 'JARVIS state reset to READY via System Tray');
          this.updateContextMenu();
        }
      },
      { type: 'separator' },
      {
        label: 'Quit JARVIS',
        click: () => {
          this.onQuit();
        }
      }
    ];

    const contextMenu = Menu.buildFromTemplate(menuTemplate);
    this.tray.setContextMenu(contextMenu);
    this.tray.setToolTip(`JARVIS — State: ${currentState}`);
  }

  public destroy(): void {
    if (this.tray) {
      this.tray.destroy();
      this.tray = null;
    }
  }
}
