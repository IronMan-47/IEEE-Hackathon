"""
JARVIS Python Agent Core — Structured Logging
"""

import logging
import sys
from datetime import datetime

class AgentLogger:
    @staticmethod
    def setup():
        logger = logging.getLogger("JARVIS_AGENT")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [PYTHON_CORE] %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

logger = AgentLogger.setup()
