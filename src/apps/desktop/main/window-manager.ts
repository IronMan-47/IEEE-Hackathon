import { BrowserWindow, screen } from 'electron';
import * as path from 'path';
import { Logger } from '../../../core/logging/logger';

export class WindowManager {
  private window: BrowserWindow | null = null;
  private isQuitting: boolean = false;

  constructor() {}

  public createWindow(preloadPath: string): BrowserWindow {
    const primaryDisplay = screen.getPrimaryDisplay();
    const { width: workWidth, height: workHeight } = primaryDisplay.workAreaSize;

    // Overlay Window Dimensions for Living Canvas Split View
    const windowWidth = 860;
    const windowHeight = 620;

    // Position in bottom-right corner of primary display
    const x = Math.max(0, workWidth - windowWidth - 24);
    const y = Math.max(0, workHeight - windowHeight - 24);

    this.window = new BrowserWindow({
      width: windowWidth,
      height: windowHeight,
      x,
      y,
      frame: false,
      transparent: true,
      alwaysOnTop: true,
      resizable: false,
      show: false,
      skipTaskbar: false,
      title: 'JARVIS — Living Canvas',
      backgroundColor: '#00000000',
      webPreferences: {
        preload: preloadPath,
        contextIsolation: true,
        nodeIntegration: false,
        sandbox: false
      }
    });

    const htmlPath = path.join(__dirname, '../renderer/index.html');
    this.window.loadFile(htmlPath);

    // Show the window once content has loaded and is ready to render
    this.window.once('ready-to-show', () => {
      if (this.window) {
        this.window.show();
        Logger.info('SHELL', 'Window ready-to-show → now visible');
      }
    });

    // Log renderer load failures for diagnostics
    this.window.webContents.on('did-fail-load', (_event, errorCode, errorDescription) => {
      Logger.error('SHELL', `Renderer failed to load: ${errorCode} ${errorDescription}`);
    });

    // Log renderer crashes
    this.window.webContents.on('render-process-gone', (_event, details) => {
      Logger.error('SHELL', `Renderer process gone: ${details.reason}`);
    });

    // Log console messages from renderer for debugging
    this.window.webContents.on('console-message', (_event, level, message) => {
      const levelStr = ['verbose', 'info', 'warning', 'error'][level] || 'unknown';
      Logger.info('RENDERER', `[${levelStr}] ${message}`);
    });

    this.window.on('close', (event) => {
      if (!this.isQuitting) {
        event.preventDefault();
        this.hide();
        Logger.info('SHELL', 'Window close intercepted -> hiding to system tray');
      }
    });

    this.window.on('closed', () => {
      this.window = null;
    });

    Logger.info('SHELL', 'JARVIS Window created', { x, y, windowWidth, windowHeight });
    return this.window;
  }

  public getWindow(): BrowserWindow | null {
    return this.window;
  }

  public isVisible(): boolean {
    return this.window !== null && this.window.isVisible();
  }

  public show(): void {
    if (this.window) {
      this.window.show();
      this.window.focus();
      Logger.info('SHELL', 'Window shown');
    }
  }

  public hide(): void {
    if (this.window && this.window.isVisible()) {
      this.window.hide();
      Logger.info('SHELL', 'Window hidden');
    }
  }

  public toggle(): boolean {
    if (this.isVisible()) {
      this.hide();
      return false;
    } else {
      this.show();
      return true;
    }
  }

  public prepareQuit(): void {
    this.isQuitting = true;
  }
}
