import { JarvisConfigPayload } from '../events/ipc-contracts';

/**
 * Centralized Configuration Manager
 */
export class ConfigManager {
  private config: JarvisConfigPayload;

  constructor(initialOverrides: Partial<JarvisConfigPayload> = {}) {
    this.config = {
      activationHotkey: 'Ctrl+Shift+Space',
      emergencyHotkey: 'Ctrl+Shift+Escape',
      startMinimized: true,
      overlayMode: 'floating',
      isDev: process.env.NODE_ENV === 'development' || !process.env.NODE_ENV,
      ...initialOverrides
    };
  }

  public getConfig(): JarvisConfigPayload {
    return { ...this.config };
  }

  public getActivationHotkey(): string {
    return this.config.activationHotkey;
  }

  public getEmergencyHotkey(): string {
    return this.config.emergencyHotkey;
  }

  public updateConfig(updates: Partial<JarvisConfigPayload>): JarvisConfigPayload {
    this.config = {
      ...this.config,
      ...updates
    };
    return this.getConfig();
  }
}
