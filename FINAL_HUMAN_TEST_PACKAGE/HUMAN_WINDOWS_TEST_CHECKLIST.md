# JARVIS - Human Windows Test Checklist

Please use this checklist to perform the final non-developer native execution test on a physical Windows Desktop. 

## A. Pre-Install Security Checks
- [ ] Ensure Microsoft Defender is enabled.
- [ ] Scan `JARVIS - The Living Canvas Setup 0.1.0.exe` manually.
- [ ] Scan `JARVIS - The Living Canvas 0.1.0.exe` (Portable) manually.
- [ ] DO NOT disable security software.
- [ ] Record any SmartScreen/Defender warnings that appear upon first execution.

## B. Installation
- [ ] Double-click the installer EXE.
- [ ] Verify the Start Menu shortcut is created.
- [ ] Launch JARVIS from the Start Menu.

## C. Startup
- [ ] Verify the JARVIS Living Canvas overlay appears.
- [ ] Wait 3-5 seconds; verify the Python backend connects (UI says READY).
- [ ] Ensure no explicit crash errors are displayed in the UI.

## D. UI Capabilities
- [ ] Toggle Compact Mode and Expanded Mode.
- [ ] Bring up the command field using `Alt+Space` or `Ctrl+Space` (check config).
- [ ] Ensure privacy indicators (Red/Green) accurately reflect states.
- [ ] Check the Task Timeline.

## E. Windows Perception
- [ ] Open a blank window in VS Code; JARVIS should detect VS Code context.
- [ ] Switch to a Browser; JARVIS should detect application change.

## F. AI Pipeline (Using `MOCK` mode)
- [ ] Submit a dummy request (e.g. "Create a hello world Python file").
- [ ] Observe intent extraction on timeline.
- [ ] Observe planning generation.
- [ ] Review the structured proposal.
- [ ] Verify Provider Status correctly claims `MOCK` (unless you supplied a real GEMINI API Key externally).

## G. Human Approval
- [ ] Click REJECT. Ensure proposal cancels.
- [ ] Request a new change. Click MODIFY. Verify it can be edited.
- [ ] Click APPROVE.

## H. Execution
- [ ] Ensure the approved change executes (if mock, observe it simulate success).
- [ ] Observe verification step complete.

## I. Safety Hardening
- [ ] Open a proposal, then close the targeted file in VS Code so the context is stale. Try to approve. Ensure it is BLOCKED.
- [ ] Try pressing the global Emergency Stop hotkey (`Ctrl+Shift+Escape`).
- [ ] Verify the overlay UI enters `SAFE_STOPPED` state immediately.
- [ ] Try approving a task while STOPPED. Ensure execution is blocked.

## J. Cross-App Verification
- [ ] Start a task in VS Code.
- [ ] Switch to a Browser. The task should ask for Browser permission.
- [ ] Switch back to VS Code. Context should return correctly.

## K. Recovery
- [ ] Close the JARVIS application normally.
- [ ] Restart JARVIS. Ensure it re-initializes without saying "Port 8765 in use".
- [ ] Terminate JARVIS abruptly (Task Manager). Restart it. Ensure crash-recovery state loads correctly.

## L. Final Result
**Result:** [ PASS / FAIL / BLOCKED ]
*Tester Observations:*
________________________________________________________
________________________________________________________
________________________________________________________
