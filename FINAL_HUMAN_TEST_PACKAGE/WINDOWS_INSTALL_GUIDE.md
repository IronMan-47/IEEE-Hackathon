# JARVIS - Windows Install Guide

## 1. System Requirements
- OS: Windows 10 or Windows 11
- Disk Space: 500 MB minimum
- Network: Active internet connection (if using real Gemini provider)

## 2. Installation
### Using the Installer (Recommended)
1. Download `JARVIS-Setup-0.1.0.exe` from the Release folder.
2. Double-click the installer and follow the setup wizard.
3. JARVIS will be installed to your local AppData directory, and a Start Menu shortcut will be created.

### Using the Portable Version
1. Download `JARVIS-Portable-0.1.0.exe` from the Release folder.
2. Double-click the executable to launch JARVIS directly without installation.

*Note: Neither Node.js nor Python is required on the host system. JARVIS packages its own embedded Python runtime.*

## 3. Configuration
JARVIS relies on a `.env` file for secure configuration. Since the packaged binary does not include internal secrets, you must provide them manually if you wish to exit MOCK mode.

1. Navigate to your installation directory (or place this next to your portable EXE).
2. Create a file named `.env`.
3. Add the following to enable the Google GenAI provider:
   ```env
   GEMINI_API_KEY=your-api-key-here
   ```
If omitted, JARVIS will gracefully fall back to the `MOCK` provider.

## 4. Usage & Demo
- The desktop application operates using a global hotkey: **`Ctrl+Shift+Space`**.
- This will toggle the Living Canvas overlay across your Windows Desktop.
- JARVIS can perceive your current application context automatically.

## 5. Emergency Stop
If at any point JARVIS acts unexpectedly or you wish to lock down operations, press:
**`Ctrl+Shift+Escape`**

This physically commands the Python Agent Core to enter a `SAFE_STOPPED` state. The runtime will actively refuse to execute further commands until you explicitly clear the emergency state from the UI.

## 6. Runtime Data & Logs
JARVIS isolates user runtime data away from the installation directory to prevent permission errors.
All snapshots, verification histories, and audit logs are safely persisted at:
`C:\Users\<Your-Username>\.jarvis\runtime` and `\.jarvis\events`

## 7. Uninstallation
To remove JARVIS completely:
1. Use "Add or Remove Programs" in Windows Settings.
2. (Optional) Manually delete the `~/.jarvis` folder to clear runtime history and audit logs.

## 8. Troubleshooting
- **Port Conflict:** If JARVIS fails to connect to the backend, ensure port `8765` is not occupied by another service on your machine.
- **Backend Not Starting:** Verify your Antivirus is not falsely flagging the embedded `jarvis-agent.exe` as it is a compiled PyInstaller executable.
