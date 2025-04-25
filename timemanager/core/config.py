# config.py
import os
import json
from pathlib import Path
from logger import log # type: ignore
TASKS_DIR = Path(__file__).resolve().parent / "config"
CONFIG_FILE = TASKS_DIR / "config.json1"

DEFAULT_CONFIG = {
    "notify": True,
    "ascii": True,
    "autostart": False,
    "silent": False,
    "default_seconds": 5,
    "use_tui_input": True
}

config = DEFAULT_CONFIG.copy()

def load_config():
    global config
    if CONFIG_FILE.exists():
        with CONFIG_FILE.open("r") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    config.update(entry)
                except json.JSONDecodeError:
                    continue
    else:
        save_config()
# === CONFIG WATCHER ===
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if Path(event.src_path) == CONFIG_FILE:
            try:
                load_config()
                log("info", "Config file updated and reloaded by config watcher.")
            except Exception as e:
                log("error", f"Config reload failed: {e}")

def start_config_daemon():
    observer = Observer()
    handler = ConfigChangeHandler()
    observer.schedule(handler, str(CONFIG_FILE.parent), recursive=False)
    thread = threading.Thread(target=observer.start, daemon=True)
    thread.start()
    log("info", "Started config file watcher daemon.")
    return thread

def save_config():
    with CONFIG_FILE.open("w") as f:
        f.write(json.dumps(config) + "\n")
