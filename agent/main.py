"""
JARVIS Python Agent Core — Application Launcher Entry Point
"""

import sys
import uvicorn
from agent.transport.api import app
from agent.core.config import config
from agent.core.logging import logger

def main():
    logger.info("==================================================")
    logger.info("JARVIS — Python Agent Core Daemon (Phase 3)")
    logger.info(f"Provider: [ {config.provider_name} ] (Mock: {config.is_mock()})")
    logger.info(f"Listening on: http://{config.host}:{config.port}")
    logger.info("==================================================")

    uvicorn.run(app, host=config.host, port=config.port, log_level="info")

if __name__ == "__main__":
    main()
