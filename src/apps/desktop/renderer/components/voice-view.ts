export class VoiceView {
  private container: HTMLElement;
  private isListening = false;
  private currentTranscript: any = null;

  constructor(containerId: string) {
    const el = document.getElementById(containerId);
    if (!el) throw new Error(`Container ${containerId} not found`);
    this.container = el;
    this.render();
  }

  public async render() {
    this.container.innerHTML = `
      <div style="background: rgba(15, 23, 42, 0.95); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 12px; padding: 20px; color: #f8fafc; font-family: 'Inter', sans-serif; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; margin-bottom: 14px;">
          <h3 style="margin: 0; display: flex; align-items: center; gap: 8px; font-size: 1rem;">
            ${this.isListening ? '<span style="color: #ef4444;">🎙 LISTENING</span>' : '<span style="color: #64748b;">🎙 MICROPHONE OFF</span>'}
          </h3>
          <div style="display: flex; gap: 8px;">
            <button id="btn-voice-toggle" style="background: ${this.isListening ? '#ef4444' : '#3b82f6'}; color: white; border: none; padding: 6px 12px; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 0.8rem;">
              ${this.isListening ? 'Stop Listening' : 'Push to Talk'}
            </button>
          </div>
        </div>

        <!-- Transcript Display -->
        ${this.currentTranscript ? `
          <div style="background: rgba(0,0,0,0.3); border: 1px solid #334155; border-radius: 8px; padding: 12px; margin-bottom: 12px;">
            <p style="margin: 0 0 8px 0; color: #94a3b8; font-size: 0.8rem;">JARVIS understood:</p>
            <p style="margin: 0 0 8px 0; color: #f8fafc; font-size: 1rem; font-weight: 500;">"${this.currentTranscript.text}"</p>
            <p style="margin: 0; color: ${this.currentTranscript.confidence === 'HIGH' ? '#10b981' : '#f59e0b'}; font-size: 0.75rem; font-weight: 700;">
              CONFIDENCE: ${this.currentTranscript.confidence}
            </p>
          </div>

          ${this.currentTranscript.confidence === 'LOW' ? `
            <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid #f59e0b; border-radius: 8px; padding: 12px;">
              <p style="margin: 0 0 10px 0; color: #fcd34d; font-size: 0.85rem;">Is this correct?</p>
              <div style="display: flex; gap: 8px;">
                <button id="btn-voice-confirm" style="background: #10b981; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 0.8rem;">Yes, Confirm</button>
                <button id="btn-voice-retry" style="background: #ef4444; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 0.8rem;">Retry</button>
              </div>
            </div>
          ` : `
            <button id="btn-voice-dismiss" style="background: #1e293b; color: white; border: 1px solid #334155; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 0.8rem;">Dismiss</button>
          `}
        ` : `
          <p style="color: #64748b; font-size: 0.85rem; margin: 0; font-style: italic;">Press 'Push to Talk' and speak your request. (Mock mode: simulates speech)</p>
        `}
      </div>
    `;

    this.attachListeners();
  }

  private attachListeners() {
    document.getElementById('btn-voice-toggle')?.addEventListener('click', async () => {
      if (!window.jarvisAPI) return;
      if (this.isListening) {
        await window.jarvisAPI.stopVoiceListening();
        this.isListening = false;
        
        // Mock sending speech processing
        const res: any = await window.jarvisAPI.processVoiceSpeech("Refactor this function", "HIGH");
        if (res && res.status === 'ROUTED') {
          this.currentTranscript = {
            text: res.command.text,
            confidence: res.command.confidence
          };
        }
      } else {
        await window.jarvisAPI.startVoiceListening();
        this.isListening = true;
        this.currentTranscript = null;
      }
      this.render();
    });

    document.getElementById('btn-voice-confirm')?.addEventListener('click', async () => {
      // confirm
      this.currentTranscript = null;
      this.render();
    });

    document.getElementById('btn-voice-retry')?.addEventListener('click', async () => {
      this.currentTranscript = null;
      this.render();
    });

    document.getElementById('btn-voice-dismiss')?.addEventListener('click', () => {
      this.currentTranscript = null;
      this.render();
    });
  }
}
