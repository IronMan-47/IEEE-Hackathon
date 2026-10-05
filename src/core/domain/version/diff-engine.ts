import { WorkspaceState, WorkspaceElement } from '../workspace/types';
import { VersionDiffResult, PropertyDiff, SpatialDiff } from './types';

export class DiffEngine {
  public static diff(
    stateA: WorkspaceState,
    stateB: WorkspaceState,
    versionAId: string = 'stateA',
    versionBId: string = 'stateB'
  ): VersionDiffResult {
    const elementsA = stateA.elements || {};
    const elementsB = stateB.elements || {};

    const added: WorkspaceElement[] = [];
    const removed: WorkspaceElement[] = [];
    const modified: PropertyDiff[] = [];
    const moved: SpatialDiff[] = [];

    const keysA = new Set(Object.keys(elementsA));
    const keysB = new Set(Object.keys(elementsB));

    // Detect Added
    for (const keyB of keysB) {
      if (!keysA.has(keyB)) {
        added.push(JSON.parse(JSON.stringify(elementsB[keyB])));
      }
    }

    // Detect Removed
    for (const keyA of keysA) {
      if (!keysB.has(keyA)) {
        removed.push(JSON.parse(JSON.stringify(elementsA[keyA])));
      }
    }

    // Detect Modified / Moved
    for (const key of keysA) {
      if (keysB.has(key)) {
        const elA = elementsA[key];
        const elB = elementsB[key];

        // Spatial diff
        if (elA.x !== elB.x || elA.y !== elB.y) {
          moved.push({
            elementId: key,
            oldX: elA.x,
            oldY: elA.y,
            newX: elB.x,
            newY: elB.y
          });
        }

        // Dimension diff
        if (elA.w !== elB.w) {
          modified.push({
            elementId: key,
            property: 'w',
            oldValue: elA.w,
            newValue: elB.w
          });
        }
        if (elA.h !== elB.h) {
          modified.push({
            elementId: key,
            property: 'h',
            oldValue: elA.h,
            newValue: elB.h
          });
        }

        // Label diff
        if ((elA.label || '') !== (elB.label || '')) {
          modified.push({
            elementId: key,
            property: 'label',
            oldValue: elA.label || '',
            newValue: elB.label || ''
          });
        }

        // Style diff
        const styleA = (elA.style || {}) as Record<string, any>;
        const styleB = (elB.style || {}) as Record<string, any>;
        const allStyleKeys = new Set([...Object.keys(styleA), ...Object.keys(styleB)]);

        for (const sKey of allStyleKeys) {
          if (styleA[sKey] !== styleB[sKey]) {
            modified.push({
              elementId: key,
              property: `style.${sKey}`,
              oldValue: styleA[sKey],
              newValue: styleB[sKey]
            });
          }
        }
      }
    }

    const identical = added.length === 0 && removed.length === 0 && modified.length === 0 && moved.length === 0;

    return {
      versionA: versionAId,
      versionB: versionBId,
      added,
      removed,
      modified,
      moved,
      identical
    };
  }
}
