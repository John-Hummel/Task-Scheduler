# ui/addtask.py
import curses
from datetime import datetime
from pathlib import Path
import sys

base_path = Path(__file__).resolve().parent.parent
sys.path.append(str(base_path / "core"))

from tasks import save_task  # type: ignore

def task_add_ui(stdscr):
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    now = datetime.now()

    name, task_type, exec_path = "", "Reminder", ""
    y, m, d, h, mi = now.year, now.month, now.day, now.hour, now.minute
    fields = ["Name", "Type", "Date", "Time", "Exec Path", "Save", "Back"]
    field_idx, subfield_idx = 0, 0

    while True:
        stdscr.clear()
        stdscr.addstr(1, 2, "Add Task - TAB=Next w/s=Up/Down  ↑↓=Adjust  ←→=Part  ENTER=Edit  Shift+S=Save  Q/ESC=Exit")

        highlight = lambda i: curses.color_pair(1) if field_idx == i else curses.A_NORMAL
        stdscr.addstr(3, 4, f"[{'>' if field_idx == 0 else ' '}] Name: {name}", highlight(0))
        stdscr.addstr(4, 4, f"[{'>' if field_idx == 1 else ' '}] Type: {task_type}", highlight(1))

        date_parts = [y, m, d]
        date_str = " ".join(f"[{val}]" if field_idx == 2 and subfield_idx == i else str(val) for i, val in enumerate(date_parts))
        stdscr.addstr(5, 4, f"[{'>' if field_idx == 2 else ' '}] Date: {date_str}", highlight(2))

        time_parts = [h, mi]
        time_str = " ".join(f"[{val:02d}]" if field_idx == 3 and subfield_idx == i else f"{val:02d}" for i, val in enumerate(time_parts))
        stdscr.addstr(6, 4, f"[{'>' if field_idx == 3 else ' '}] Time: {time_str}", highlight(3))

        stdscr.addstr(7, 4, f"[{'>' if field_idx == 4 else ' '}] Exec Path: {exec_path if task_type == 'Executable' else '(N/A)'}", highlight(4))
        stdscr.addstr(8, 4, "[>] Save", highlight(5))
        stdscr.addstr(9, 4, "[>] Back", highlight(6))

        stdscr.refresh()
        key = stdscr.getch()

        if key in [ord('q'), 27]: break
        if key == ord('w') and subfield_idx == 0:
            field_idx = (field_idx - 1) % len(fields)

        elif key == 9 or key == ord('s'):
            field_idx = (field_idx + 1) % len(fields)
            subfield_idx = 0
        elif key in [curses.KEY_LEFT, curses.KEY_RIGHT]:
            if field_idx == 2:
                subfield_idx = (subfield_idx + (1 if key == curses.KEY_RIGHT else -1)) % 3
            elif field_idx == 3:
                subfield_idx = (subfield_idx + (1 if key == curses.KEY_RIGHT else -1)) % 2
        elif key in [curses.KEY_UP, curses.KEY_DOWN]:
            delta = 1 if key == curses.KEY_UP else -1
            if field_idx == 2:
                if subfield_idx == 0: y += delta
                elif subfield_idx == 1: m = max(1, min(12, m + delta))
                elif subfield_idx == 2: d = max(1, min(31, d + delta))
            elif field_idx == 3:
                if subfield_idx == 0: h = (h + delta) % 24
                elif subfield_idx == 1: mi = (mi + delta) % 60
        elif key in [10, 13]:
            curses.echo()
            if field_idx == 0:
                stdscr.addstr(11, 4, "Enter Task Name: ")
                name = stdscr.getstr(11, 22, 40).decode()
            elif field_idx == 1:
                task_type = "Executable" if task_type == "Reminder" else "Reminder"
            elif field_idx == 4 and task_type == "Executable":
                stdscr.addstr(11, 4, "Exec Path: ")
                exec_path = stdscr.getstr(11, 16, 60).decode()
            elif field_idx == 6:
                break
            curses.noecho()
        elif key in [ord('s'), ord('S')] or field_idx == 5:
            dt = datetime(y, m, d, h, mi)
            task = {
                "task_name": name,
                "task_type": task_type,
                "datetime": dt.strftime("%Y-%m-%d %H:%M"),
                "exec_path": exec_path if task_type == "Executable" else "",
                "recurrence": "None",
                "interval": 0
            }
            save_task(task)
            break
def launch_add_task_window():

    curses.wrapper(task_add_ui)
def add_task_window():
    import sys
    import subprocess
    add_task_script = Path(__file__).parent / "launchaddtask.py"
    interpreter = sys.executable
    # Launch in new terminal window per OS
    if sys.platform.startswith("win"):
        subprocess.Popen(["start", "cmd", "/c", interpreter, str(add_task_script)], shell=True)
    elif sys.platform.startswith("linux"):
        subprocess.Popen(["x-terminal-emulator", "-e", interpreter, str(add_task_script)])
    elif sys.platform == "darwin":
        subprocess.Popen(["osascript", "-e", f'tell app "Terminal" to do script "{interpreter} {add_task_script}"'])
    else:
        print("Unsupported platform for subprocess terminal execution.")

