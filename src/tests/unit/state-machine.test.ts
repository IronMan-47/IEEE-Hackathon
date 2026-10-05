import { describe, it, expect, beforeEach, vi } from 'vitest';
import { JarvisStateMachine } from '../../core/state/state-machine';
import { JarvisState, JarvisStateEvent } from '../../core/state/types';

describe('JarvisStateMachine Unit Tests', () => {
  let sm: JarvisStateMachine;

  beforeEach(() => {
    sm = new JarvisStateMachine();
  });

  it('starts in IDLE state', () => {
    expect(sm.getState()).toBe(JarvisState.IDLE);
  });

  it('transitions from IDLE to READY on INITIALIZE', () => {
    const ok = sm.transition(JarvisStateEvent.INITIALIZE);
    expect(ok).toBe(true);
    expect(sm.getState()).toBe(JarvisState.READY);
  });

  it('transitions from READY to ACTIVE on ACTIVATE', () => {
    sm.transition(JarvisStateEvent.INITIALIZE);
    const ok = sm.transition(JarvisStateEvent.ACTIVATE);
    expect(ok).toBe(true);
    expect(sm.getState()).toBe(JarvisState.ACTIVE);
  });

  it('transitions from ACTIVE to READY on DEACTIVATE', () => {
    sm.transition(JarvisStateEvent.INITIALIZE);
    sm.transition(JarvisStateEvent.ACTIVATE);
    const ok = sm.transition(JarvisStateEvent.DEACTIVATE);
    expect(ok).toBe(true);
    expect(sm.getState()).toBe(JarvisState.READY);
  });

  it('transitions to STOPPED state on EMERGENCY_STOP from any state', () => {
    sm.transition(JarvisStateEvent.INITIALIZE);
    sm.transition(JarvisStateEvent.ACTIVATE);

    const ok = sm.transition(JarvisStateEvent.EMERGENCY_STOP, 'Test Emergency');
    expect(ok).toBe(true);
    expect(sm.getState()).toBe(JarvisState.STOPPED);
  });

  it('BLOCKS ACTIVATE when state is STOPPED', () => {
    sm.transition(JarvisStateEvent.INITIALIZE);
    sm.transition(JarvisStateEvent.EMERGENCY_STOP);
    expect(sm.getState()).toBe(JarvisState.STOPPED);

    // Attempt activation while stopped
    const ok = sm.transition(JarvisStateEvent.ACTIVATE);
    expect(ok).toBe(false); // Transition must be rejected!
    expect(sm.getState()).toBe(JarvisState.STOPPED);
  });

  it('allows RESET_TO_READY from STOPPED state', () => {
    sm.transition(JarvisStateEvent.INITIALIZE);
    sm.transition(JarvisStateEvent.EMERGENCY_STOP);
    expect(sm.getState()).toBe(JarvisState.STOPPED);

    const ok = sm.transition(JarvisStateEvent.RESET_TO_READY);
    expect(ok).toBe(true);
    expect(sm.getState()).toBe(JarvisState.READY);
  });

  it('notifies registered listeners on state change', () => {
    const listener = vi.fn();
    sm.subscribe(listener);

    sm.transition(JarvisStateEvent.INITIALIZE, 'Booting');
    expect(listener).toHaveBeenCalledTimes(1);
    expect(listener).toHaveBeenCalledWith(expect.objectContaining({
      fromState: JarvisState.IDLE,
      toState: JarvisState.READY,
      event: JarvisStateEvent.INITIALIZE,
      reason: 'Booting'
    }));
  });
});
