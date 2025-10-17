"""
Config file watcher - Auto-reload Flask when config files change

Monitors:
- config/config.yaml
- config/config.local.yaml
- config/.env

When changes are detected, automatically restarts the Flask process.
"""

import os
import sys
import time
import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigWatcher:
    """Watch configuration files and restart Flask on changes"""

    def __init__(self, project_root):
        """
        Args:
            project_root: Path to project root directory
        """
        self.project_root = Path(project_root)
        self.config_dir = self.project_root / 'config'

        # Files to watch
        self.watched_files = [
            self.config_dir / 'config.yaml',
            self.config_dir / 'config.local.yaml',
            self.config_dir / '.env',
        ]

        # Track modification times
        self.mtimes = {}
        for filepath in self.watched_files:
            if filepath.exists():
                self.mtimes[str(filepath)] = filepath.stat().st_mtime

        self.running = False
        self.thread = None

    def start(self, check_interval=2.0):
        """
        Start watching config files in background thread

        Args:
            check_interval: How often to check for changes (seconds)
        """
        if self.running:
            logger.warning("Config watcher already running")
            return

        self.running = True
        self.thread = threading.Thread(
            target=self._watch_loop,
            args=(check_interval,),
            daemon=True,
            name='ConfigWatcher'
        )
        self.thread.start()

        watched_names = [f.name for f in self.watched_files if f.exists()]
        watched_paths = [str(f) for f in self.watched_files if f.exists()]
        logger.info(f"Config watcher started (monitoring: {', '.join(watched_names)})")
        logger.debug(f"Watching paths: {watched_paths}")

    def stop(self):
        """Stop the watcher thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

    def _watch_loop(self, check_interval):
        """Background thread that checks for file changes"""
        logger.debug("Config watcher loop starting")
        while self.running:
            try:
                self._check_for_changes()
                time.sleep(check_interval)
            except Exception as e:
                logger.error(f"Config watcher error: {e}", exc_info=True)
                time.sleep(check_interval)
        logger.debug("Config watcher loop stopped")

    def _check_for_changes(self):
        """Check if any watched files have been modified"""
        for filepath in self.watched_files:
            if not filepath.exists():
                # File was deleted or doesn't exist
                if str(filepath) in self.mtimes:
                    logger.warning(f"Config file deleted: {filepath.name}")
                    del self.mtimes[str(filepath)]
                continue

            current_mtime = filepath.stat().st_mtime
            previous_mtime = self.mtimes.get(str(filepath))

            if previous_mtime is None:
                # New file appeared
                logger.info(f"New config file detected: {filepath.name}")
                self.mtimes[str(filepath)] = current_mtime
                self._reload_config(f"New config file: {filepath.name}")
            elif current_mtime > previous_mtime:
                # File was modified
                logger.info(f"Config file changed: {filepath.name}")
                self.mtimes[str(filepath)] = current_mtime
                self._reload_config(f"Config changed: {filepath.name}")

    def _reload_config(self, reason):
        """
        Reload configuration without restarting Flask

        Args:
            reason: Human-readable reason for reload
        """
        logger.info(f"Reloading config: {reason}")

        try:
            from lib.config import reload_config
            reload_config()
            logger.info("Config reloaded successfully")
        except Exception as e:
            logger.error(f"Failed to reload config: {e}", exc_info=True)


def start_watcher(app):
    """
    Convenience function to start config watcher for a Flask app

    Args:
        app: Flask app instance

    Returns:
        ConfigWatcher instance (already started)
    """
    project_root = Path(__file__).parent.parent
    watcher = ConfigWatcher(project_root)
    watcher.start()

    # Register cleanup on app teardown
    @app.teardown_appcontext
    def cleanup_watcher(exception=None):
        watcher.stop()

    return watcher


# For testing
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    project_root = Path(__file__).parent.parent
    watcher = ConfigWatcher(project_root)
    watcher.start()

    print("Config watcher running. Modify config files to test. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        watcher.stop()
