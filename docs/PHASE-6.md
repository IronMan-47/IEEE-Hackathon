# Phase 6: Real Windows Screen Perception & Active Application Detection

## Overview
Phase 6 establishes the first real desktop perception layer for **JARVIS**.
JARVIS moves beyond the reference Living Canvas environment to observe real Windows applications (e.g. VS Code, Chrome, Figma, Windows Terminal) directly on the user's desktop.

> **Authoritative Phase 6 Principle**:  
> **"Phase 6 sees — it does NOT act."**  
> Perception is strictly read-only. JARVIS captures active window identity, process metadata, window bounds, screen geometry, and optional on-demand window screenshots under explicit user policy control. JARVIS is given ZERO authority or permission to move the mouse, simulate clicks, or issue keystrokes in Phase 6.

---

## 1. Perception Architecture

```
                                REAL WINDOWS DESKTOP
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │                                               │
        Active Window Info                               Screen Geometry
     (ctypes user32/psutil)                           (GDI / PIL ImageGrab)
                 │                                               │
                 └───────────────────────┬───────────────────────┘
                                         │
                             PerceptionPolicyManager
                      (PERCEIVE_ENABLED / Excluded Apps)
                                         │
                                   CaptureManager
                                         │
                                  AppClassifier
                  (CODE_EDITOR, BROWSER, DESIGN_TOOL, etc.)
                                         │
                                  ContextBuilder
                                         │
                                 PerceptionResult
                                         │
                              FastAPI /agent/perceive
                                         │
                              JARVIS Python Agent Core
```

---

## 2. Core Perception Components

### 1. Active Window Detection (`WindowsWindowProvider`)
* **Implementation**: [agent/perception/active_window.py](file:///c:/Users/lenovo/OneDrive/Desktop/Hackathons/Jarvis%20-%20Living%20Assistent/agent/perception/active_window.py)
* Uses native Windows Win32 API calls via Python `ctypes`:
  - `user32.GetForegroundWindow()` $\rightarrow$ HWND handle of active active window.
  - `user32.GetWindowTextW(hwnd)` $\rightarrow$ Active window title (e.g., `"main.py — JARVIS - Visual Studio Code"`).
  - `user32.GetWindowRect(hwnd)` $\rightarrow$ Active window boundary coordinates ($x, y, w, h$).
  - `user32.GetWindowThreadProcessId(hwnd)` $\rightarrow$ PID of process owning the active window.
  - `psutil.Process(pid).name()` $\rightarrow$ Executable process name (e.g., `Code.exe`, `chrome.exe`).
  - `psutil.Process(pid).exe()` $\rightarrow$ Full executable path on disk.

### 2. On-Demand Screen & Window Capture (`WindowsScreenProvider`)
* **Implementation**: [agent/perception/screen.py](file:///c:/Users/lenovo/OneDrive/Desktop/Hackathons/Jarvis%20-%20Living%20Assistent/agent/perception/screen.py)
* Performs explicit on-demand screen or active window crop capture:
  - Uses `PIL.ImageGrab.grab(bbox=...)` with fallback to native Windows GDI `BitBlt` (`user32.GetDC(0)` $\rightarrow$ `gdi32.BitBlt` $\rightarrow$ `GetDIBits`).
  - Converts image to Base64 in memory (`data_base64`).
  - **Zero Continuous Capture**: Screenshots are captured strictly upon explicit user request or authorized perception call.

### 3. Application Classification (`AppClassifier`)
* **Implementation**: [agent/perception/classifier.py](file:///c:/Users/lenovo/OneDrive/Desktop/Hackathons/Jarvis%20-%20Living%20Assistent/agent/perception/classifier.py)
* Categorizes active applications into high-level domains:
  - `CODE_EDITOR`: `Code.exe`, `devenv.exe`, `pycharm64.exe`, `idea64.exe`, `sublime_text.exe`.
  - `BROWSER`: `chrome.exe`, `msedge.exe`, `firefox.exe`, `brave.exe`, `opera.exe`.
  - `DESIGN_TOOL`: `figma.exe`, `photoshop.exe`, `illustrator.exe`, `acad.exe`.
  - `TERMINAL`: `cmd.exe`, `powershell.exe`, `wt.exe`, `bash.exe`.
  - `DOCUMENT_EDITOR`: `winword.exe`, `excel.exe`, `powerpnt.exe`, `notepad.exe`.
  - `UNKNOWN`: Default fallback for uncategorized processes.

### 4. Privacy & Excluded Application Boundary (`PerceptionPolicyManager`)
* **Implementation**: [agent/perception/policy.py](file:///c:/Users/lenovo/OneDrive/Desktop/Hackathons/Jarvis%20-%20Living%20Assistent/agent/perception/policy.py)
* **Policy Toggles**: Supports `PERCEPTION_ENABLED` and `PERCEPTION_DISABLED` global modes.
* **Sensitive Application Blacklist**: Automatically blocks screen capture when active process matches sensitive process list (e.g. `1Password.exe`, `KeePass.exe`, `Bitwarden.exe`).
* **Privacy-Safe Dict Logging**: `PerceptionResult.to_summary_dict()` automatically strips raw Base64 pixel string (`data_base64`) from all ordinary logs.

### 5. Desktop Context Abstraction (`ContextBuilder`)
* **Implementation**: [agent/context/perception_context.py](file:///c:/Users/lenovo/OneDrive/Desktop/Hackathons/Jarvis%20-%20Living%20Assistent/agent/context/perception_context.py)
* Introduces `ContextSource` enum (`LIVING_CANVAS` vs `DESKTOP_PERCEPTION`), structuring perception outputs for the AI reasoning engine.

---

## 3. Data Schema (`PerceptionResult`)

```python
class PerceptionResult(BaseModel):
    timestamp: int
    active_application: ApplicationIdentity
    active_window: ActiveWindowInfo
    screen_metadata: ScreenMetadata
    capture_metadata: CaptureMetadata
    classification: AppClassification
    perception_enabled: bool
    is_excluded: bool
```

---

## 4. Safety & Emergency Stop Integration
- When system enters `STOPPED` state (Emergency Stop triggered via `Ctrl+Shift+F12` or UI), `CaptureManager` **HARD-BLOCKS** desktop perception and window capture, returning `perception_enabled: False`.

---

## 5. Verification & Test Metrics

### 1. Automated Test Suite (63 Total Unit Tests Passing)
* **Python Pytest Suite (`18/18` Passed)**:
  - `test_perception.py`: Active window detection, mock providers, screen capture, app classifier, privacy policy, excluded applications, emergency stop barrier, context builder.
  - `test_agent.py`, `test_providers.py`, `test_sanitizer.py`.
* **TypeScript Vitest Suite (`45/45` Passed)**:
  - `version-graph.test.ts`, `safety-hardening.test.ts`, `workspace-domain.test.ts`, `state-machine.test.ts`, `config.test.ts`, `logger.test.ts`.

### 2. Runtime Execution on Windows Desktop
* **FastAPI Perception Endpoints**:
  - `POST /agent/perceive`: Returns structured JSON summary of active application, window bounds, classification, and optional Base64 capture.
  - `POST /agent/perceive/policy`: Toggles global perception policy.
* **Electron Renderer UI**:
  - Displays **Desktop Perception Panel** with live active process, window title, bounds, classification badge, perception toggle button, on-demand "Perceive Now" trigger, and thumbnail preview.
