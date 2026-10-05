# JARVIS - Final Release Capability Matrix

This matrix describes the absolute physical capabilities embedded in the Phase 21 final packaged release. This establishes an honest baseline of what JARVIS is capable of executing vs what is simulated for demonstration.

| Component | Capability Status | Reason / Explanation |
|---|---|---|
| **Gemini AI Engine** | **MOCK** (Default) | The bundled EXE does NOT contain hardcoded API keys. If run normally, it defaults to a mock generator. External `.env` configuration is required to achieve **REAL GEMINI** status. |
| **Windows GUI / Overlay** | **REAL** | Built with Electron + React. Fully natively interactive. |
| **VS Code Integration** | **REAL** | Native Context Fusion works across active VS Code instances. |
| **Human Approval System** | **REAL** | Execution Barriers enforce cryptographic token signatures. |
| **Emergency Stop** | **REAL** | Bound via global hotkey (`Ctrl+Shift+Escape`), instantly triggering the FastAPI backend interrupt. |
| **Browser Execution** | **PROPOSAL-ONLY** | JARVIS will scrape browser context, but it cannot click or navigate autonomously. |
| **Voice Processing** | **SIMULATED** | Voice is restricted to mock text-injection for Beta stability. |
| **Visual Processing** | **SIMULATED** | Screenshot endpoints are mocked in production builds to prevent privacy leakage of native Desktop frames. |
| **Terminal Automation** | **UNAVAILABLE** | Fully locked out. OS-level arbitrary code execution is strictly blocked by the Safety Barrier. |
| **Figma Integration** | **UNAVAILABLE** | Plugin bridges were removed to ensure Windows platform focus. |

*Note to Tester: Do not expect JARVIS to autonomously navigate your mouse, type in your terminal, or click on websites in this release. All functionality explicitly requires structured Proposal approval.*
