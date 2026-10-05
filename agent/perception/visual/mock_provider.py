"""
JARVIS Python Agent Core — Phase 13 Mock Vision Provider
Provides deterministic, reproducible mock visual screen perception scenarios
(VS Code, Browser, Figma, Living Canvas, Login, Dialog, Unknown) for unit testing and offline development.
"""

from typing import Optional, Dict, Any
from agent.perception.types import PerceptionResult
from agent.perception.visual.models import VisualContext, ProvenanceSource
from agent.perception.visual.provider import VisionProvider
from agent.perception.visual.sanitizer import VisualSanitizer


class MockVisionProvider(VisionProvider):
    def analyze_screen(
        self,
        perception_result: PerceptionResult,
        image_bytes: Optional[bytes] = None,
        scenario: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> VisualContext:
        """
        Generates structured visual context based on scenario override or active application classification.
        """
        sc = (scenario or "").upper().strip()

        if not sc:
            app_name = perception_result.active_application.name.lower()
            win_title = perception_result.active_window.title.lower()

            if "code" in app_name or "vs code" in win_title:
                sc = "VS_CODE_SCREEN"
            elif "chrome" in app_name or "browser" in win_title or "living canvas" in win_title:
                if "checkout" in win_title or "canvas" in win_title:
                    sc = "LIVING_CANVAS_SCREEN"
                else:
                    sc = "BROWSER_SCREEN"
            elif "figma" in app_name or "figma" in win_title:
                sc = "FIGMA_SCREEN"
            elif "login" in win_title or "auth" in win_title:
                sc = "LOGIN_SCREEN"
            elif "error" in win_title or "dialog" in win_title:
                sc = "DIALOG_SCREEN"
            else:
                sc = "UNKNOWN_SCREEN"

        raw_dict = self._build_raw_scenario_data(sc, perception_result)
        return VisualSanitizer.sanitize(raw_dict, perception_result, source=ProvenanceSource.VISION_MODEL)

    def _build_raw_scenario_data(self, scenario: str, perception: PerceptionResult) -> Dict[str, Any]:
        ts = perception.timestamp or 1700000000000

        if scenario == "VS_CODE_SCREEN":
            return {
                "context_id": f"vctx_vscode_{ts}",
                "application": "Visual Studio Code",
                "application_class": "CODE_EDITOR",
                "confidence": 0.98,
                "visual_summary": "VS Code is active. A Python code file is open in the main editor, a file explorer is on the left, and a terminal panel is visible at the bottom.",
                "bounds": {"x": 0, "y": 0, "width": 1920, "height": 1080},
                "regions": [
                    {"id": "reg_sidebar", "name": "File Explorer Sidebar", "bounds": {"x": 0, "y": 40, "width": 300, "height": 1040}, "element_ids": ["elem_sidebar_header", "elem_file_tree"]},
                    {"id": "reg_editor", "name": "Main Code Editor", "bounds": {"x": 300, "y": 40, "width": 1620, "height": 700}, "element_ids": ["elem_code_tab", "elem_code_lines"]},
                    {"id": "reg_terminal", "name": "Terminal Panel", "bounds": {"x": 300, "y": 740, "width": 1620, "height": 340}, "element_ids": ["elem_term_output"]}
                ],
                "elements": [
                    {"id": "elem_sidebar_header", "type": "HEADING", "role": "heading", "bounds": {"x": 10, "y": 50, "width": 280, "height": 30}, "text": "EXPLORER", "confidence": 0.99},
                    {"id": "elem_file_tree", "type": "LIST", "role": "list", "bounds": {"x": 10, "y": 90, "width": 280, "height": 900}, "text": "main.py\nconfig.py\nutils.py", "confidence": 0.95},
                    {"id": "elem_code_tab", "type": "TAB", "role": "tab", "bounds": {"x": 310, "y": 45, "width": 150, "height": 35}, "text": "main.py", "confidence": 0.99},
                    {"id": "elem_code_lines", "type": "CODE_REGION", "role": "region", "bounds": {"x": 310, "y": 90, "width": 1580, "height": 630}, "text": "def add(a, b):\n    return a + b\n", "confidence": 0.97},
                    {"id": "elem_term_output", "type": "PANEL", "role": "term", "bounds": {"x": 310, "y": 750, "width": 1580, "height": 320}, "text": "PS C:\\workspace> python -m pytest tests/python", "confidence": 0.96}
                ]
            }

        elif scenario == "BROWSER_SCREEN":
            return {
                "context_id": f"vctx_browser_{ts}",
                "application": "Google Chrome",
                "application_class": "BROWSER",
                "confidence": 0.96,
                "visual_summary": "Google Chrome is active. Showing search navigation bar and main content section with action buttons.",
                "bounds": {"x": 0, "y": 0, "width": 1920, "height": 1080},
                "regions": [
                    {"id": "reg_navbar", "name": "Browser Navigation Bar", "bounds": {"x": 0, "y": 0, "width": 1920, "height": 80}, "element_ids": ["elem_url_bar", "elem_search_btn"]},
                    {"id": "reg_content", "name": "Web Page Content", "bounds": {"x": 0, "y": 80, "width": 1920, "height": 1000}, "element_ids": ["elem_heading", "elem_card_1", "elem_btn_action"]}
                ],
                "elements": [
                    {"id": "elem_url_bar", "type": "INPUT", "role": "textbox", "bounds": {"x": 200, "y": 20, "width": 1200, "height": 40}, "text": "https://example.com/docs", "confidence": 0.99},
                    {"id": "elem_search_btn", "type": "BUTTON", "role": "button", "bounds": {"x": 1410, "y": 20, "width": 80, "height": 40}, "text": "Search", "confidence": 0.95},
                    {"id": "elem_heading", "type": "HEADING", "role": "heading", "bounds": {"x": 300, "y": 120, "width": 800, "height": 50}, "text": "JARVIS Living Canvas Documentation", "confidence": 0.98},
                    {"id": "elem_card_1", "type": "CARD", "role": "region", "bounds": {"x": 300, "y": 200, "width": 600, "height": 300}, "text": "Documentation content card", "confidence": 0.92},
                    {"id": "elem_btn_action", "type": "BUTTON", "role": "button", "bounds": {"x": 320, "y": 440, "width": 150, "height": 40}, "text": "Learn More", "confidence": 0.97}
                ]
            }

        elif scenario == "LIVING_CANVAS_SCREEN":
            return {
                "context_id": f"vctx_canvas_{ts}",
                "application": "JARVIS Living Canvas",
                "application_class": "BROWSER",
                "confidence": 0.99,
                "visual_summary": "JARVIS Living Canvas reference workspace active containing main container card, Pay Now button, and subtotal summary.",
                "bounds": {"x": 0, "y": 0, "width": 1920, "height": 1080},
                "regions": [
                    {"id": "reg_canvas_main", "name": "Living Canvas Stage", "bounds": {"x": 100, "y": 100, "width": 800, "height": 600}, "element_ids": ["card_main", "btn_pay", "txt_subtotal"]}
                ],
                "elements": [
                    {"id": "card_main", "type": "CARD", "role": "container", "bounds": {"x": 100, "y": 100, "width": 800, "height": 600}, "text": "Checkout Demo Workspace Container", "confidence": 0.99},
                    {"id": "btn_pay", "type": "BUTTON", "role": "button", "bounds": {"x": 150, "y": 500, "width": 200, "height": 50}, "text": "Pay Now", "confidence": 0.98},
                    {"id": "txt_subtotal", "type": "TEXT", "role": "text", "bounds": {"x": 150, "y": 450, "width": 300, "height": 30}, "text": "Subtotal: $100.00", "confidence": 0.97}
                ]
            }

        elif scenario == "FIGMA_SCREEN":
            return {
                "context_id": f"vctx_figma_{ts}",
                "application": "Figma",
                "application_class": "DESIGN_TOOL",
                "confidence": 0.95,
                "visual_summary": "Figma is active. Canvas showing UI mockup layout with layer tree panel on left.",
                "bounds": {"x": 0, "y": 0, "width": 1920, "height": 1080},
                "regions": [
                    {"id": "reg_figma_layers", "name": "Layers Panel", "bounds": {"x": 0, "y": 40, "width": 240, "height": 1040}, "element_ids": ["elem_layer_list"]},
                    {"id": "reg_figma_stage", "name": "Design Canvas Stage", "bounds": {"x": 240, "y": 40, "width": 1680, "height": 1040}, "element_ids": ["elem_frame_1"]}
                ],
                "elements": [
                    {"id": "elem_layer_list", "type": "LIST", "role": "list", "bounds": {"x": 10, "y": 50, "width": 220, "height": 900}, "text": "Frame 1\nHeader Component\nPrimary Button", "confidence": 0.93},
                    {"id": "elem_frame_1", "type": "CARD", "role": "group", "bounds": {"x": 350, "y": 150, "width": 800, "height": 600}, "text": "Desktop Wireframe Layout", "confidence": 0.96}
                ]
            }

        elif scenario == "LOGIN_SCREEN":
            return {
                "context_id": f"vctx_login_{ts}",
                "application": "Secure Login Dialog",
                "application_class": "DOCUMENT_EDITOR",
                "confidence": 0.97,
                "visual_summary": "Authentication login screen visible containing username field, password input field, and Submit button.",
                "bounds": {"x": 400, "y": 200, "width": 600, "height": 400},
                "regions": [
                    {"id": "reg_auth", "name": "Authentication Form", "bounds": {"x": 400, "y": 200, "width": 600, "height": 400}, "element_ids": ["input_user", "input_password", "btn_submit"]}
                ],
                "elements": [
                    {"id": "input_user", "type": "INPUT", "role": "textbox", "bounds": {"x": 450, "y": 250, "width": 500, "height": 40}, "text": "user@example.com", "confidence": 0.98},
                    {"id": "input_password", "type": "INPUT", "role": "textbox", "bounds": {"x": 450, "y": 320, "width": 500, "height": 40}, "text": "secret_password_123", "confidence": 0.98},
                    {"id": "btn_submit", "type": "BUTTON", "role": "button", "bounds": {"x": 450, "y": 390, "width": 150, "height": 40}, "text": "Login", "confidence": 0.97}
                ]
            }

        elif scenario == "DIALOG_SCREEN":
            return {
                "context_id": f"vctx_dialog_{ts}",
                "application": "System Error Dialog",
                "application_class": "UNKNOWN",
                "confidence": 0.99,
                "visual_summary": "System error dialog open displaying module exception error text.",
                "bounds": {"x": 500, "y": 300, "width": 500, "height": 250},
                "regions": [
                    {"id": "reg_dialog_main", "name": "Dialog Window", "bounds": {"x": 500, "y": 300, "width": 500, "height": 250}, "element_ids": ["elem_dlg_title", "elem_dlg_msg", "elem_dlg_ok"]}
                ],
                "elements": [
                    {"id": "elem_dlg_title", "type": "DIALOG", "role": "alert", "bounds": {"x": 510, "y": 310, "width": 480, "height": 30}, "text": "Unhandled Exception", "confidence": 0.99},
                    {"id": "elem_dlg_msg", "type": "TEXT", "role": "text", "bounds": {"x": 510, "y": 350, "width": 480, "height": 80}, "text": "ModuleNotFoundError: No module named 'invalid_module'", "confidence": 0.98},
                    {"id": "elem_dlg_ok", "type": "BUTTON", "role": "button", "bounds": {"x": 700, "y": 450, "width": 100, "height": 35}, "text": "OK", "confidence": 0.99}
                ]
            }

        else:  # UNKNOWN_SCREEN
            return {
                "context_id": f"vctx_unknown_{ts}",
                "application": perception.active_application.name or "Unknown Application",
                "application_class": "UNKNOWN",
                "confidence": 0.50,
                "visual_summary": f"Active window '{perception.active_window.title}' of unknown application classification.",
                "bounds": {"x": 0, "y": 0, "width": perception.screen_metadata.active_width or 1920, "height": perception.screen_metadata.active_height or 1080},
                "regions": [
                    {"id": "reg_main", "name": "Window Area", "bounds": {"x": 0, "y": 0, "width": 800, "height": 600}, "element_ids": ["elem_window_title"]}
                ],
                "elements": [
                    {"id": "elem_window_title", "type": "TEXT", "role": "title", "bounds": {"x": 10, "y": 10, "width": 400, "height": 30}, "text": perception.active_window.title or "Unknown Window", "confidence": 0.60}
                ]
            }
