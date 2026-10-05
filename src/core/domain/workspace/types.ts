/**
 * Living Canvas Workspace Domain Types
 * Pure types for elements, layout properties, and patch operations.
 */

export type ElementType = 'heading' | 'text' | 'button' | 'card' | 'input' | 'container';

export interface ElementStyle {
  fill?: string;
  color?: string;
  fontSize?: number;
  fontWeight?: number | string;
  borderRadius?: number;
  borderWidth?: number;
  borderColor?: string;
  padding?: number;
  opacity?: number;
}

export interface WorkspaceElement {
  id: string;
  type: ElementType;
  x: number;
  y: number;
  w: number;
  h: number;
  label?: string;
  parentId?: string;
  style: ElementStyle;
}

export interface WorkspaceState {
  revision: number;
  title: string;
  elements: Record<string, WorkspaceElement>;
  lastUpdated: number;
}

export enum PatchOperationType {
  CREATE_ELEMENT = 'CREATE_ELEMENT',
  UPDATE_ELEMENT = 'UPDATE_ELEMENT',
  DELETE_ELEMENT = 'DELETE_ELEMENT',
  MOVE_ELEMENT = 'MOVE_ELEMENT',
  RESIZE_ELEMENT = 'RESIZE_ELEMENT',
  UPDATE_STYLE = 'UPDATE_STYLE',
  UPDATE_TEXT = 'UPDATE_TEXT',
  GROUP_ELEMENTS = 'GROUP_ELEMENTS',
  UNGROUP_ELEMENTS = 'UNGROUP_ELEMENTS'
}

export interface PatchOperation {
  op: PatchOperationType;
  targetId: string;
  previousValue?: Record<string, unknown>;
  proposedValue: Record<string, unknown>;
  reason: string;
}

export interface InverseOperation {
  op: PatchOperationType;
  targetId: string;
  restoreValue: Record<string, unknown>;
}
