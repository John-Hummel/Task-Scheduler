from pathlib import Path
import sys
base_path = Path(__file__).resolve().parent
for folder in ["core", "ui"]:
    sys.path.append(str(base_path / folder))
print(f"Base path: {base_path}")

from config import load_config, config,start_config_daemon  # type: ignore
from tasks import get_all_tasks, save_task  # type: ignore
from tui import launch_tui # type: ignore
from daemons import start_daemon # type: ignore
if __name__ == "__main__":
    load_config()
    start_config_daemon()
    start_daemon()
    get_all_tasks()
    if config.get("use_tui_input"):
        launch_tui()
    else:
        print("GUI mode not implemented yet.")
