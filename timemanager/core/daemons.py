from pathlib import Path
import platform
import subprocess
import threading
import time
from datetime import datetime
import uuid

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from logger import log
from config import config
from tasks import (
    get_all_tasks, delete_task, save_task, load_task_file, TASKS_DIR
)

SCRIPTS_DIR = Path(__file__).resolve().parent / "scripts"
SCRIPTS_DIR.mkdir(exist_ok=True)

# === ASCII Script Generation ===
def generate_ascii_script_content(task_name, exec_path):
    return f"""import os, time, platform, subprocess
from pyfiglet import Figlet

fig = Figlet(font='slant')
for i in range({config['default_seconds']}, 0, -1):
    os.system('cls' if platform.system() == 'Windows' else 'clear')
    print(fig.renderText(f"{task_name} {{i}}s left"))
    time.sleep(1)
subprocess.run({repr(exec_path)}, shell=True)
time.sleep(2)
os.remove(__file__)
"""

def write_ascii_script(task_name, exec_path, prefix="launch"):
    filename = f"{prefix}_{task_name.replace(' ', '_')}_{uuid.uuid4().hex[:6]}.py"
    path = SCRIPTS_DIR / filename
    with open(path, "w") as f:
        f.write(generate_ascii_script_content(task_name, exec_path))
    return path

# === Task Watcher ===
class TaskCreationHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.endswith(".json1"):
            try:
                task = load_task_file(event.src_path)
                if task.get("task_type") == "Executable" and config.get("ascii"):
                    script_path = write_ascii_script(task["task_name"], task["exec_path"], prefix="scheduled")
                    task["script_path"] = str(script_path)
                    save_task(task)
                    log("info", f"Script created for new task: {task['task_name']}")
            except Exception as e:
                log("error", f"Failed to handle new task file: {e}")

def start_task_watcher():
    observer = Observer()
    observer.schedule(TaskCreationHandler(), str(TASKS_DIR), recursive=False)
    observer.start()
    log("info", "Started filesystem watcher on tasks directory")

# === ASCII Launcher ===
def launch_ascii_terminal(task_name, exec_path):
    try:
        script_path = write_ascii_script(task_name, exec_path)
        system = platform.system()
        if system == "Windows":
            subprocess.Popen(f'start cmd /c python {script_path}', shell=True)
        elif system == "Linux":
            subprocess.Popen(["x-terminal-emulator", "-e", f"python3 {script_path}"])
        elif system == "Darwin":
            subprocess.Popen(["osascript", "-e", f'tell app "Terminal" to do script \"python3 {script_path}\"'])
        else:
            subprocess.run(exec_path, shell=True)
        log("info", f"Launched ASCII countdown for {task_name}")
    except Exception as e:
        log("error", f"Failed ASCII launch for {task_name}: {e}")
        subprocess.run(exec_path, shell=True)

# === Notifications ===
def notify_reminder(task_name):
    try:
        from plyer import notification
        notification.notify(title="Reminder", message=f"Time to do: {task_name}", timeout=5)
        log("info", f"Notification sent for reminder: {task_name}")
    except Exception as e:
        log("error", f"Notification failed for {task_name}: {e}")

# === Task Execution ===
def execute_task(task):
    name = task.get("task_name")
    is_exec = task.get("task_type") == "Executable"
    if is_exec:
        exec_path = task.get("exec_path", "")
        if config.get("ascii"):
            launch_ascii_terminal(name, exec_path)
        else:
            subprocess.run(exec_path, shell=True)
            log("info", f"Executed: {exec_path}")
    else:
        notify_reminder(name)

# === Scheduler Loop ===
def scheduler_loop():
    log("info", "Scheduler loop started")
    while True:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        tasks = get_all_tasks()
        for task in tasks.values():
            if task.get("datetime") == now_str:
                execute_task(task)
                if task.get("recurrence") != "None":
                    # future recurring logic
                    pass
                else:
                    delete_task(task["task_name"])

        time.sleep(5)

# === Daemon Entry ===
def start_daemon():
    threading.Thread(target=scheduler_loop, daemon=True).start()
    start_task_watcher()
    log("info", "Scheduler and watcher daemons started.")
