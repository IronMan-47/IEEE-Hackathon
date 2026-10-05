import { createHash } from 'crypto';
import { WorkspaceState } from '../workspace/types';

/**
 * Computes deterministic canonical SHA-256 hash for a given workspace state.
 * Guarantee: Independent of object key order or UI rendering order.
 */
export class CanonicalHash {
  public static hashState(state: WorkspaceState): string {
    const canonicalObject = CanonicalHash.normalizeState(state);
    const jsonString = JSON.stringify(canonicalObject);
    return createHash('sha256').update(jsonString).digest('hex');
  }

  public static verifyStateHash(state: WorkspaceState, expectedHash: string): boolean {
    const computedHash = CanonicalHash.hashState(state);
    return computedHash === expectedHash;
  }

  private static normalizeState(state: WorkspaceState): Record<string, unknown> {
    const sortedElementKeys = Object.keys(state.elements || {}).sort();
    const normalizedElements: Record<string, unknown> = {};

    for (const key of sortedElementKeys) {
      const el = state.elements[key];
      normalizedElements[key] = {
        id: el.id,
        type: el.type,
        x: el.x,
        y: el.y,
        w: el.w,
        h: el.h,
        label: el.label || '',
        style: CanonicalHash.sortObject(el.style || {})
      };
    }

    return {
      title: state.title || '',
      revision: state.revision,
      elements: normalizedElements
    };
  }

  private static sortObject(obj: Record<string, any>): Record<string, any> {
    const sortedKeys = Object.keys(obj).sort();
    const result: Record<string, any> = {};
    for (const key of sortedKeys) {
      result[key] = obj[key];
    }
    return result;
  }
}
