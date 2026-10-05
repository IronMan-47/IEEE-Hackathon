import { describe, it, expect } from 'vitest';
import { IPCChannel } from '../../core/events/ipc-contracts';

describe('Phase 13 — Visual Perception & Inspection Unit Tests', () => {
  it('defines Phase 13 IPC channels for visual perception', () => {
    expect(IPCChannel.VISUAL_ANALYZE_SCREEN).toBe('jarvis:visual-analyze-screen');
    expect(IPCChannel.VISUAL_GET_CURRENT_CONTEXT).toBe('jarvis:visual-get-current-context');
    expect(IPCChannel.VISUAL_CLEAR_CONTEXT).toBe('jarvis:visual-clear-context');
    expect(IPCChannel.VISUAL_EVALUATE_GROUND_TRUTH).toBe('jarvis:visual-evaluate-ground-truth');
  });

  it('validates mock visual context structure', () => {
    const mockContext = {
      context_id: 'vctx_test_123',
      application: 'Visual Studio Code',
      application_class: 'CODE_EDITOR',
      confidence: 0.98,
      confidence_level: 'HIGH_CONFIDENCE',
      provenance: 'VISION_MODEL',
      elements: [
        { id: 'elem_1', type: 'BUTTON', text: 'Run Test', bounds: { x: 10, y: 20, width: 80, height: 30 }, confidence: 0.95 }
      ],
      visual_summary: 'VS Code is active.'
    };

    expect(mockContext.context_id).toBe('vctx_test_123');
    expect(mockContext.confidence_level).toBe('HIGH_CONFIDENCE');
    expect(mockContext.elements.length).toBe(1);
    expect(mockContext.elements[0].type).toBe('BUTTON');
  });
});
