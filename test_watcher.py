#!/usr/bin/env python
"""
Test config watcher locally
"""

import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)-7s] [%(name)-10s] %(message)s'
)

logger = logging.getLogger(__name__)

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.config_watcher import ConfigWatcher

def main():
    project_root = Path(__file__).parent
    watcher = ConfigWatcher(project_root)

    logger.info("Starting watcher test...")
    logger.info(f"Project root: {project_root}")
    logger.info(f"Watched files: {[str(f) for f in watcher.watched_files]}")
    logger.info(f"Initial mtimes: {watcher.mtimes}")

    watcher.start(check_interval=1.0)  # Check every 1 second

    logger.info("Watcher started. Modify config/config.yaml to test. Press Ctrl+C to exit.")

    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping...")
        watcher.stop()

if __name__ == '__main__':
    main()
