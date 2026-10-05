import os
import json
import threading
from typing import Callable, Dict, List, Any
from agent.runtime.models import AgentEvent
from agent.core.logging import logger

class EventBus:
    def __init__(self, storage_dir: str | None = None):
        self._subscribers: Dict[str, List[Callable[[AgentEvent], None]]] = {}
        self._events: List[AgentEvent] = []
        self._sequence_counter = 0
        self._lock = threading.RLock()
        if storage_dir is None:
            home = os.path.expanduser("~")
            storage_dir = os.path.join(home, ".jarvis", "events")
        self.storage_dir = storage_dir
        self.event_log_file = os.path.join(self.storage_dir, "event_log.jsonl")
        
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)
            
        self._processed_events: set = set()

    def subscribe(self, event_type: str, handler: Callable[[AgentEvent], None]):
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(handler)

    def publish(self, event: AgentEvent):
        with self._lock:
            # Idempotency check
            if event.event_id in self._processed_events:
                logger.warn(f"Duplicate event skipped: {event.event_id}")
                return
            self._processed_events.add(event.event_id)
            
            # Ordering
            self._sequence_counter += 1
            event.sequence = self._sequence_counter
            
            self._events.append(event)
            self._persist_event(event)

            handlers = self._subscribers.get(event.event_type, [])
            all_handlers = self._subscribers.get("*", [])
            
        # Dispatch outside the lock to avoid deadlocks
        for handler in handlers + all_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error handling event {event.event_id}: {str(e)}")

    def _persist_event(self, event: AgentEvent):
        try:
            with open(self.event_log_file, "a", encoding="utf-8") as f:
                f.write(event.model_dump_json() + "\\n")
        except Exception as e:
            logger.error(f"Failed to persist event {event.event_id}: {str(e)}")

    def get_events(self, limit: int = 100) -> List[AgentEvent]:
        with self._lock:
            return self._events[-limit:]
