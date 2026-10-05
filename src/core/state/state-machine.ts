import { JarvisState, JarvisStateEvent, StateChangeEvent, StateChangeListener } from './types';

/**
 * Authoritative JARVIS State Machine
 * Prevents invalid state transitions and enforces Emergency Stop safety constraints.
 */
export class JarvisStateMachine {
  private currentState: JarvisState = JarvisState.IDLE;
  private listeners: StateChangeListener[] = [];
  private lastErrorMessage?: string;

  constructor(initialState: JarvisState = JarvisState.IDLE) {
    this.currentState = initialState;
  }

  public getState(): JarvisState {
    return this.currentState;
  }

  public isReady(): boolean {
    return this.currentState !== JarvisState.STOPPED && this.currentState !== JarvisState.ERROR;
  }

  public getLastError(): string | undefined {
    return this.lastErrorMessage;
  }

  public subscribe(listener: StateChangeListener): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  /**
   * Transition the state machine using a defined event.
   * Throws an error or returns false if transition is prohibited.
   */
  public transition(event: JarvisStateEvent, reason?: string): boolean {
    const fromState = this.currentState;
    let nextState: JarvisState | null = null;

    switch (event) {
      case JarvisStateEvent.EMERGENCY_STOP:
        // Emergency Stop is valid from ANY state
        nextState = JarvisState.STOPPED;
        break;

      case JarvisStateEvent.FAIL:
        // Failure can occur from ANY state
        nextState = JarvisState.ERROR;
        if (reason) {
          this.lastErrorMessage = reason;
        }
        break;

      case JarvisStateEvent.INITIALIZE:
        if (fromState === JarvisState.IDLE || fromState === JarvisState.ERROR) {
          nextState = JarvisState.READY;
        }
        break;

      case JarvisStateEvent.ACTIVATE:
        if (fromState === JarvisState.READY) {
          nextState = JarvisState.ACTIVE;
        } else if (fromState === JarvisState.STOPPED) {
          // Block activation while in STOPPED state! Must reset to READY first.
          return false;
        }
        break;

      case JarvisStateEvent.DEACTIVATE:
        if (fromState === JarvisState.ACTIVE) {
          nextState = JarvisState.READY;
        }
        break;

      case JarvisStateEvent.RESET_TO_READY:
        if (fromState === JarvisState.STOPPED || fromState === JarvisState.ERROR || fromState === JarvisState.IDLE) {
          nextState = JarvisState.READY;
          this.lastErrorMessage = undefined;
        }
        break;

      default:
        break;
    }

    if (nextState !== null && nextState !== fromState) {
      this.currentState = nextState;
      const changeEvent: StateChangeEvent = {
        fromState,
        toState: nextState,
        event,
        timestamp: Date.now(),
        reason
      };

      this.notifyListeners(changeEvent);
      return true;
    }

    return false;
  }

  private notifyListeners(event: StateChangeEvent): void {
    for (const listener of this.listeners) {
      try {
        listener(event);
      } catch (err) {
        console.error('[StateMachine] Listener error:', err);
      }
    }
  }
}
