from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class AppClassification(str, Enum):
    CODE_EDITOR = "CODE_EDITOR"
    BROWSER = "BROWSER"
    DESIGN_TOOL = "DESIGN_TOOL"
    TERMINAL = "TERMINAL"
    DOCUMENT_EDITOR = "DOCUMENT_EDITOR"
    UNKNOWN = "UNKNOWN"

class ApplicationIdentity(BaseModel):
    id: str = Field(default="app_unknown")
    name: str = Field(default="Unknown Application")
    process_name: str = Field(default="unknown.exe")
    executable_path: Optional[str] = Field(default=None)
    pid: Optional[int] = Field(default=None)

class ActiveWindowInfo(BaseModel):
    title: str = Field(default="Unknown Window")
    x: int = Field(default=0)
    y: int = Field(default=0)
    width: int = Field(default=0)
    height: int = Field(default=0)
    is_minimized: bool = Field(default=False)
    monitor_index: int = Field(default=0)

class ScreenMetadata(BaseModel):
    monitor_count: int = Field(default=1)
    primary_width: int = Field(default=1920)
    primary_height: int = Field(default=1080)
    active_width: int = Field(default=1920)
    active_height: int = Field(default=1080)
    dpi_scale: float = Field(default=1.0)

class CaptureMetadata(BaseModel):
    captured: bool = Field(default=False)
    capture_type: Optional[str] = Field(default=None) # ACTIVE_WINDOW | FULL_SCREEN
    timestamp: Optional[int] = Field(default=None)
    format: Optional[str] = Field(default="PNG")
    data_base64: Optional[str] = Field(default=None, exclude=True) # Explicitly excluded from dict dump for privacy/logging safety

class PerceptionPolicy(BaseModel):
    enabled: bool = Field(default=True)
    excluded_apps: List[str] = Field(default_factory=lambda: ["1Password.exe", "KeePass.exe", "Bitwarden.exe"])

class PerceptionResult(BaseModel):
    timestamp: int = Field(default=0)
    active_application: ApplicationIdentity = Field(default_factory=ApplicationIdentity)
    active_window: ActiveWindowInfo = Field(default_factory=ActiveWindowInfo)
    screen_metadata: ScreenMetadata = Field(default_factory=ScreenMetadata)
    capture_metadata: CaptureMetadata = Field(default_factory=CaptureMetadata)
    classification: AppClassification = Field(default=AppClassification.UNKNOWN)
    perception_enabled: bool = Field(default=True)
    is_excluded: bool = Field(default=False)

    def to_summary_dict(self) -> Dict[str, Any]:
        """Returns safe summary dict excluding raw screenshot pixels for logging."""
        d = self.model_dump()
        if "capture_metadata" in d:
            d["capture_metadata"].pop("data_base64", None)
        return d
