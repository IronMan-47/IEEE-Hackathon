import { describe, it, expect } from 'vitest';
import { ConfigManager } from '../../core/config/config-manager';

describe('ConfigManager Unit Tests', () => {
  it('returns default configuration settings', () => {
    const mgr = new ConfigManager();
    const config = mgr.getConfig();

    expect(config.activationHotkey).toBe('Ctrl+Shift+Space');
    expect(config.emergencyHotkey).toBe('Ctrl+Shift+Escape');
    expect(config.startMinimized).toBe(true);
  });

  it('allows updating configuration options', () => {
    const mgr = new ConfigManager();
    const updated = mgr.updateConfig({ activationHotkey: 'Ctrl+Alt+J' });

    expect(updated.activationHotkey).toBe('Ctrl+Alt+J');
    expect(mgr.getActivationHotkey()).toBe('Ctrl+Alt+J');
    expect(mgr.getEmergencyHotkey()).toBe('Ctrl+Shift+Escape');
  });
});
