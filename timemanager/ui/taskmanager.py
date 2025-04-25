import curses
from datetime import datetime
from pathlib import Path 
import sys

base_path = Path(__file__).resolve().parent.parent
for folder in ["core", "ui"]:
    sys.path.append(str(base_path / folder))
print(f"Base path: {base_path}")
from config import load_config, config, save_config # type: ignore

def taskmanager_ui():
    def task_manager_ui(stdscr):
        from tasks import delete_task, get_all_tasks # type: ignore

        tasks=get_all_tasks()
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        selected = 0

        while True:
            stdscr.clear()
            stdscr.addstr(1, 2, "Task Manager - ↑↓: Navigate, ENTER: Remove Task, Q: Quit")

            task_list = list(tasks.keys())
            for i, task in enumerate(task_list):
                highlight = curses.color_pair(1) if i == selected else curses.A_NORMAL
                stdscr.addstr(3 + i, 4, f"{i + 1}. {task}", highlight)

            key = stdscr.getch()
            if key in [ord('q'), 27]:  # Q or ESC
                sys.exit(0)
            elif key == ord('r'):
                break
            elif key == curses.KEY_UP and selected > 0:
                selected -= 1
            elif key == curses.KEY_DOWN and selected < len(task_list) - 1:
                selected += 1
            elif key in [curses.KEY_ENTER, ord('\n')]:
                if 0 <= selected < len(task_list):
                    delete_task(task_list[selected])
    curses.wrapper(task_manager_ui)
    taskmanager_ui()

from pathlib import Path

def launch_task_manager_window():
    import subprocess
    taskmanager_path = Path(__file__).resolve().parent / "taskmanagerlaunch.py"
    interpreter = sys.executable
    
    # Launch in new terminal window per OS
    if sys.platform.startswith("win"):
        subprocess.Popen(["start", "cmd", "/c", interpreter, str(taskmanager_path)], shell=True)
    elif sys.platform.startswith("linux"):
        subprocess.Popen(["x-terminal-emulator", "-e", interpreter, str(taskmanager_path)])
    elif sys.platform == "darwin":
        subprocess.Popen(["osascript", "-e", f'tell app "Terminal" to do script "{interpreter} {taskmanager_path}"'])
    else:
        print("Unsupported platform for subprocess terminal execution.")
