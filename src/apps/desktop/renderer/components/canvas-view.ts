import { WorkspaceState, WorkspaceElement } from '../../../../core/domain/workspace/types';
import { Proposal } from '../../../../core/domain/proposal/types';

export class CanvasView {
  constructor(private container: HTMLElement) {}

  public render(state: WorkspaceState, proposal?: Proposal | null): void {
    this.container.innerHTML = '';

    const canvasRoot = document.createElement('div');
    canvasRoot.className = 'living-canvas-root';

    // Render Revision Badge Header
    const headerBar = document.createElement('div');
    headerBar.className = 'canvas-header-bar';
    headerBar.innerHTML = `
      <span class="canvas-title">${state.title}</span>
      <span class="revision-badge">Rev ${state.revision}</span>
    `;
    canvasRoot.appendChild(headerBar);

    const viewport = document.createElement('div');
    viewport.className = 'canvas-viewport';

    // Render elements
    for (const el of Object.values(state.elements)) {
      const elNode = this.createElementNode(el);

      // Check if proposal touches this element -> render Ghost Overlay
      if (proposal && (proposal.status === 'PENDING' || proposal.status === 'MODIFIED')) {
        const matchingOp = proposal.operations.find(op => op.targetId === el.id);
        if (matchingOp) {
          const ghostOverlay = this.createGhostOverlayNode(el, matchingOp.proposedValue);
          viewport.appendChild(ghostOverlay);
        }
      }

      viewport.appendChild(elNode);
    }

    canvasRoot.appendChild(viewport);
    this.container.appendChild(canvasRoot);
  }

  private createElementNode(el: WorkspaceElement): HTMLElement {
    const div = document.createElement('div');
    div.className = `canvas-element el-${el.type}`;
    div.id = `node_${el.id}`;

    div.style.left = `${el.x}px`;
    div.style.top = `${el.y}px`;
    div.style.width = `${el.w}px`;
    div.style.height = `${el.h}px`;

    if (el.style.fill) div.style.backgroundColor = el.style.fill;
    if (el.style.color) div.style.color = el.style.color;
    if (el.style.fontSize) div.style.fontSize = `${el.style.fontSize}px`;
    if (el.style.fontWeight) div.style.fontWeight = String(el.style.fontWeight);
    if (el.style.borderRadius) div.style.borderRadius = `${el.style.borderRadius}px`;
    if (el.style.borderColor) div.style.borderColor = el.style.borderColor;
    if (el.style.borderWidth) {
      div.style.borderStyle = 'solid';
      div.style.borderWidth = `${el.style.borderWidth}px`;
    }

    if (el.label) {
      div.textContent = el.label;
    }

    return div;
  }

  private createGhostOverlayNode(el: WorkspaceElement, proposedValue: Record<string, unknown>): HTMLElement {
    const ghost = document.createElement('div');
    ghost.className = 'canvas-ghost-overlay';

    const targetX = typeof proposedValue.x === 'number' ? proposedValue.x : el.x;
    const targetY = typeof proposedValue.y === 'number' ? proposedValue.y : el.y;
    const targetW = typeof proposedValue.w === 'number' ? proposedValue.w : el.w;
    const targetH = typeof proposedValue.h === 'number' ? proposedValue.h : el.h;

    ghost.style.left = `${targetX}px`;
    ghost.style.top = `${targetY}px`;
    ghost.style.width = `${targetW}px`;
    ghost.style.height = `${targetH}px`;

    if (proposedValue.style && typeof (proposedValue.style as any).fill === 'string') {
      ghost.style.backgroundColor = (proposedValue.style as any).fill;
    }

    ghost.innerHTML = `<span class="ghost-badge">AI Proposal Preview</span>`;
    return ghost;
  }
}
