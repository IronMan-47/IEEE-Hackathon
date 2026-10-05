import sys
import ctypes
from abc import ABC, abstractmethod
from typing import Tuple
from agent.perception.types import ApplicationIdentity, ActiveWindowInfo, ScreenMetadata

try:
    import psutil
except ImportError:
    psutil = None

class WindowProvider(ABC):
    @abstractmethod
    def get_active_window(self) -> Tuple[ApplicationIdentity, ActiveWindowInfo, ScreenMetadata]:
        pass

class WindowsWindowProvider(WindowProvider):
    def get_active_window(self) -> Tuple[ApplicationIdentity, ActiveWindowInfo, ScreenMetadata]:
        if sys.platform != "win32":
            return self._fallback_unknown()

        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return self._fallback_unknown()

            # Window Title
            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value or "Active Window"

            # Window Bounds (RECT)
            rect = ctypes.wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            x = rect.left
            y = rect.top
            w = max(0, rect.right - rect.left)
            h = max(0, rect.bottom - rect.top)

            # PID & Process Name
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            process_id = pid.value

            process_name = "unknown.exe"
            exe_path = None
            if psutil and process_id > 0:
                try:
                    proc = psutil.Process(process_id)
                    process_name = proc.name()
                    exe_path = proc.exe()
                except Exception:
                    pass

            app_id = ApplicationIdentity(
                id=f"app_{process_name.replace('.exe', '')}_{process_id}",
                name=process_name.replace(".exe", "").capitalize(),
                process_name=process_name,
                executable_path=exe_path,
                pid=process_id
            )

            win_info = ActiveWindowInfo(
                title=title,
                x=x,
                y=y,
                width=w,
                height=h,
                is_minimized=user32.IsIconic(hwnd) != 0,
                monitor_index=0
            )

            # Monitor Metadata
            screen_w = user32.GetSystemMetrics(0) # SM_CXSCREEN
            screen_h = user32.GetSystemMetrics(1) # SM_CYSCREEN
            mon_count = user32.GetSystemMetrics(80) # SM_CMONITORS
            
            screen_info = ScreenMetadata(
                monitor_count=max(1, mon_count),
                primary_width=screen_w,
                primary_height=screen_h,
                active_width=screen_w,
                active_height=screen_h,
                dpi_scale=1.0
            )

            return app_id, win_info, screen_info

        except Exception as err:
            print(f"[WindowsWindowProvider] Error querying active window: {err}")
            return self._fallback_unknown()

    def _fallback_unknown(self) -> Tuple[ApplicationIdentity, ActiveWindowInfo, ScreenMetadata]:
        return (
            ApplicationIdentity(id="app_unknown", name="Unknown Application", process_name="unknown.exe"),
            ActiveWindowInfo(title="Unknown Desktop Window", x=0, y=0, width=1920, height=1080),
            ScreenMetadata(monitor_count=1, primary_width=1920, primary_height=1080)
        )

class MockWindowProvider(WindowProvider):
    def __init__(self, scenario: str = "VS_CODE"):
        self.scenario = scenario

    def get_active_window(self) -> Tuple[ApplicationIdentity, ActiveWindowInfo, ScreenMetadata]:
        if self.scenario == "VS_CODE":
            return (
                ApplicationIdentity(id="app_code_1234", name="Visual Studio Code", process_name="Code.exe", pid=1234),
                ActiveWindowInfo(title="main.py — JARVIS - Visual Studio Code", x=100, y=80, width=1400, height=900),
                ScreenMetadata(monitor_count=1, primary_width=1920, primary_height=1080)
            )
        elif self.scenario == "CHROME":
            return (
                ApplicationIdentity(id="app_chrome_5678", name="Google Chrome", process_name="chrome.exe", pid=5678),
                ActiveWindowInfo(title="GitHub - JARVIS Agent - Google Chrome", x=0, y=0, width=1920, height=1040),
                ScreenMetadata(monitor_count=1, primary_width=1920, primary_height=1080)
            )
        elif self.scenario == "FIGMA":
            return (
                ApplicationIdentity(id="app_figma_9101", name="Figma", process_name="Figma.exe", pid=9101),
                ActiveWindowInfo(title="Living Canvas UI Kit – Figma", x=200, y=100, width=1500, height=850),
                ScreenMetadata(monitor_count=1, primary_width=1920, primary_height=1080)
            )
        else:
            return (
                ApplicationIdentity(id="app_unknown_9999", name="Unknown", process_name="unknown.exe", pid=9999),
                ActiveWindowInfo(title="Desktop Workspace", x=0, y=0, width=800, height=600),
                ScreenMetadata(monitor_count=1, primary_width=1920, primary_height=1080)
            )
