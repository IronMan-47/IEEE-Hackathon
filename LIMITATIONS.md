# Known Limitations

JARVIS was deliberately constructed as a bounded, defensible product. It favors safety over broad capabilities.

1. **No Universal Desktop Automation**: We explicitly removed all generic `pyautogui`, `pynput`, or `os.system` execution capabilities. JARVIS relies exclusively on semantic `DomainExecutors`.
2. **Limited Executable Domains**: Execution is strictly limited to the Phase 2 Living Canvas, Visual Studio Code (via adapter), and Chromium-based browsers (via adapter).
3. **No Automatic Application Launching**: JARVIS cannot open VS Code if it's closed. The human user must steer the OS environment.
4. **Visual Latency**: Vision-based validation processes incur heavy LLM latency, bounding operation speed.
5. **Irreversible Browser Operations**: While VS Code and Canvas edits can be instantly rolled back via the Version Graph, browser operations (e.g. `CLICK`) are stateful external mutations that cannot be automatically reverted.
6. **Strict Staleness Rejection**: If a user modifies a file manually by even a single byte while JARVIS is proposing a change, JARVIS will permanently reject the Proposal due to hash mismatch. The user must initiate a new cycle.
7. **Single Monitor Fallback**: Multi-monitor perception defaults to the primary monitor if OS active window hooks fail.
8. **Simulated Voice API**: Voice recognition currently uses the `MockSTTProvider`. To support native voice, an integration with a cloud speech API is required.
