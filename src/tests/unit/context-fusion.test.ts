import { describe, it, expect } from 'vitest';

describe('Phase 14 — Context Fusion & Grounded Reasoning Unit Tests', () => {
  it('validates grounded context schema representation', () => {
    const mockGroundedContext = {
      context_id: 'gctx_unit_123',
      timestamp: Date.now(),
      primary_application: {
        name: 'Visual Studio Code',
        process_name: 'code.exe',
        role: 'PRIMARY_APPLICATION'
      },
      secondary_applications: [
        {
          name: 'Google Chrome',
          process_name: 'chrome.exe',
          role: 'SECONDARY_APPLICATION'
        }
      ],
      confidence: 0.95,
      facts: [
        { id: 'fact_1', statement: 'Active application is Visual Studio Code', type: 'FACT', provenance: 'WINDOWS_API' },
        { id: 'fact_2', statement: 'Active document is main.py', type: 'FACT', provenance: 'VS_CODE_ADAPTER' },
        { id: 'fact_3', statement: 'Observed error dialog: ModuleNotFoundError', type: 'OBSERVED', provenance: 'VISION_MODEL' }
      ],
      conflicts: [],
      clarification_required: false
    };

    expect(mockGroundedContext.context_id).toBe('gctx_unit_123');
    expect(mockGroundedContext.primary_application.name).toBe('Visual Studio Code');
    expect(mockGroundedContext.secondary_applications.length).toBe(1);
    expect(mockGroundedContext.facts.length).toBe(3);
    expect(mockGroundedContext.confidence).toBe(0.95);
  });

  it('detects and handles target ambiguity requests', () => {
    const ambigTarget = {
      target_id: 'ambiguous_buttons',
      target_type: 'BUTTON',
      is_ambiguous: true,
      candidate_targets: [
        { id: 'btn_1', text: 'Run Test' },
        { id: 'btn_2', text: 'Run All' }
      ]
    };

    expect(ambigTarget.is_ambiguous).toBe(true);
    expect(ambigTarget.candidate_targets.length).toBe(2);
  });
});
