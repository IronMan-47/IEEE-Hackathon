import os
import json
from typing import Optional
from agent.runtime.models import RuntimeSnapshot
from agent.core.logging import logger

class RuntimePersistence:
    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir is None:
            home = os.path.expanduser("~")
            storage_dir = os.path.join(home, ".jarvis", "runtime")
        self.storage_dir = storage_dir
        self.snapshot_file = os.path.join(self.storage_dir, "snapshot.json")
        
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)

    def save_snapshot(self, snapshot: RuntimeSnapshot):
        try:
            # Atomic write pattern
            temp_file = self.snapshot_file + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(snapshot.model_dump_json(indent=2))
            os.replace(temp_file, self.snapshot_file)
            logger.info(f"Runtime snapshot saved: {snapshot.snapshot_id}")
        except Exception as e:
            logger.error(f"Failed to save runtime snapshot: {str(e)}")

    def load_snapshot(self) -> Optional[RuntimeSnapshot]:
        if not os.path.exists(self.snapshot_file):
            return None
        try:
            with open(self.snapshot_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return RuntimeSnapshot(**data)
        except Exception as e:
            logger.error(f"Failed to load runtime snapshot due to corruption or schema mismatch: {str(e)}")
            raise ValueError(f"Corrupted snapshot: {e}")
