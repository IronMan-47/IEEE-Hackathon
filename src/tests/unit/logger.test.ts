import { describe, it, expect, vi } from 'vitest';
import { Logger } from '../../core/logging/logger';

describe('Logger Unit Tests', () => {
  it('logs structured info messages without error', () => {
    const spy = vi.spyOn(console, 'log').mockImplementation(() => {});
    Logger.info('SHELL', 'Test message', { key: 'value' });

    expect(spy).toHaveBeenCalled();
    spy.mockRestore();
  });
});
