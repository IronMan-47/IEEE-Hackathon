/**
 * JARVIS State Machine Types
 * Authoritative State & Transition definitions for Phase 1 Desktop Agent
 */

export enum JarvisState {
  IDLE = 'IDLE',
  READY = 'READY',
  ACTIVE = 'ACTIVE',
  STOPPED = 'STOPPED',
  ERROR = 'ERROR'
}

export enum JarvisStateEvent {
  INITIALIZE = 'INITIALIZE',
  ACTIVATE = 'ACTIVATE',
  DEACTIVATE = 'DEACTIVATE',
  EMERGENCY_STOP = 'EMERGENCY_STOP',
  RESET_TO_READY = 'RESET_TO_READY',
  FAIL = 'FAIL'
}

export interface StateChangeEvent {
  fromState: JarvisState;
  toState: JarvisState;
  event: JarvisStateEvent;
  timestamp: number;
  reason?: string;
}

export type StateChangeListener = (event: StateChangeEvent) => void;
