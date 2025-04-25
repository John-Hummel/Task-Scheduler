import os
import json
from datetime import datetime
from pathlib import Path
from logger import log

TASKS_DIR = Path(__file__).resolve().parent / "tasks"

def _task_path(name):
    return os.path.join(TASKS_DIR, f"{name}.json1")

def save_task(data):
    name = data.get("task_name")
    if name:
        with open(_task_path(name), "w") as f:
            f.write(json.dumps(data) + "\n")
        log("info", f"Task saved: {name}")

def delete_task(name):
    path = _task_path(name)
    if os.path.exists(path):
        os.remove(path)
        log("info", f"Task deleted: {name}")

def get_all_tasks():
    tasks = {}
    for fname in os.listdir(TASKS_DIR):
        if fname.endswith(".json1") and fname != "config.json1":
            try:
                with open(os.path.join(TASKS_DIR, fname)) as f:
                    for line in f:
                        if line.strip():
                            task = json.loads(line.strip())
                            task_name = task.get("task_name")
                            if task_name:
                                tasks[task_name] = task
            except Exception as e:
                log("warning", f"Failed to read task file {fname}: {e}")
    return tasks

def load_task_file(filepath):
    try:
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    return json.loads(line)
    except Exception as e:
        log("error", f"Failed to load task from {filepath}: {e}")
    return {}

def read_task_log(task_name):
    log_path = os.path.join(TASKS_DIR, f"{task_name}.log.json1")
    if not os.path.exists(log_path):
        return []
    try:
        with open(log_path) as f:
            return [json.loads(line.strip()) for line in f if line.strip()]
    except Exception as e:
        log("error", f"Failed to read log for task {task_name}: {e}")
        return []
