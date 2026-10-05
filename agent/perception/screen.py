import io
import sys
import base64
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from agent.perception.types import CaptureMetadata

try:
    from PIL import ImageGrab, Image, ImageDraw
except ImportError:
    ImageGrab = None
    Image = None
    ImageDraw = None

class ScreenProvider(ABC):
    @abstractmethod
    def capture_window(self, bbox: Optional[Tuple[int, int, int, int]] = None) -> CaptureMetadata:
        pass

class WindowsScreenProvider(ScreenProvider):
    def capture_window(self, bbox: Optional[Tuple[int, int, int, int]] = None) -> CaptureMetadata:
        if not Image:
            return CaptureMetadata(captured=False)

        img = None
        cap_type = "FULL_SCREEN"

        # 1. Try ImageGrab
        if ImageGrab:
            try:
                if bbox and bbox[2] > 0 and bbox[3] > 0:
                    crop_box = (max(0, bbox[0]), max(0, bbox[1]), max(0, bbox[0]) + bbox[2], max(0, bbox[1]) + bbox[3])
                    img = ImageGrab.grab(bbox=crop_box)
                    cap_type = "ACTIVE_WINDOW"
                else:
                    img = ImageGrab.grab()
                    cap_type = "FULL_SCREEN"
            except Exception:
                img = None

        # 2. Try GDI BitBlt Fallback on Windows
        if img is None and sys.platform == "win32":
            try:
                img = self._gdi_capture(bbox)
                cap_type = "ACTIVE_WINDOW" if (bbox and bbox[2] > 0) else "FULL_SCREEN"
            except Exception as err:
                print(f"[WindowsScreenProvider] GDI capture failed: {err}")
                img = None

        if img is None:
            return CaptureMetadata(captured=False)

        try:
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            b64_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

            return CaptureMetadata(
                captured=True,
                capture_type=cap_type,
                timestamp=0,
                format="PNG",
                data_base64=b64_data
            )
        except Exception as err:
            print(f"[WindowsScreenProvider] Image encoding failed: {err}")
            return CaptureMetadata(captured=False)

    def _gdi_capture(self, bbox: Optional[Tuple[int, int, int, int]] = None) -> Optional[Image.Image]:
        import ctypes

        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [
                ('biSize', ctypes.c_uint32),
                ('biWidth', ctypes.c_int32),
                ('biHeight', ctypes.c_int32),
                ('biPlanes', ctypes.c_uint16),
                ('biBitCount', ctypes.c_uint16),
                ('biCompression', ctypes.c_uint32),
                ('biSizeImage', ctypes.c_uint32),
                ('biXPelsPerMeter', ctypes.c_int32),
                ('biYPelsPerMeter', ctypes.c_int32),
                ('biClrUsed', ctypes.c_uint32),
                ('biClrImportant', ctypes.c_uint32),
            ]

        class BITMAPINFO(ctypes.Structure):
            _fields_ = [
                ('bmiHeader', BITMAPINFOHEADER),
                ('bmiColors', ctypes.c_uint32 * 3),
            ]

        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32

        if bbox and bbox[2] > 0 and bbox[3] > 0:
            left, top, width, height = max(0, bbox[0]), max(0, bbox[1]), bbox[2], bbox[3]
        else:
            left, top = 0, 0
            width = user32.GetSystemMetrics(0)
            height = user32.GetSystemMetrics(1)

        hdc_screen = user32.GetDC(0)
        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
        hbmp = gdi32.CreateCompatibleBitmap(hdc_screen, width, height)
        gdi32.SelectObject(hdc_mem, hbmp)

        gdi32.BitBlt(hdc_mem, 0, 0, width, height, hdc_screen, left, top, 0x00CC0020)

        bmpinfo = BITMAPINFO()
        bmpinfo.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmpinfo.bmiHeader.biWidth = width
        bmpinfo.bmiHeader.biHeight = -height
        bmpinfo.bmiHeader.biPlanes = 1
        bmpinfo.bmiHeader.biBitCount = 32
        bmpinfo.bmiHeader.biCompression = 0

        buffer = ctypes.create_string_buffer(width * height * 4)
        gdi32.GetDIBits(hdc_screen, hbmp, 0, height, buffer, ctypes.byref(bmpinfo), 0)

        user32.ReleaseDC(0, hdc_screen)
        gdi32.DeleteDC(hdc_mem)
        gdi32.DeleteObject(hbmp)

        return Image.frombuffer("RGBA", (width, height), buffer, "raw", "BGRA", 0, 1)

class MockScreenProvider(ScreenProvider):
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail

    def capture_window(self, bbox: Optional[Tuple[int, int, int, int]] = None) -> CaptureMetadata:
        if self.should_fail:
            return CaptureMetadata(captured=False)

        if Image and ImageDraw:
            img = Image.new("RGB", (100, 100), color=(15, 23, 42))
            draw = ImageDraw.Draw(img)
            draw.text((10, 40), "JARVIS MOCK", fill=(56, 189, 248))

            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            b64_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
        else:
            b64_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        return CaptureMetadata(
            captured=True,
            capture_type="MOCK_ACTIVE_WINDOW",
            timestamp=0,
            format="PNG",
            data_base64=b64_data
        )
