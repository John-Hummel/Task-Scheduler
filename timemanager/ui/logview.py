
import curses
import os
from pathlib import Path
from datetime import datetime
import subprocess
import platform

LOG_DIR = Path(__file__).resolve().parent.parent /'core'/ "logs"
print(f"Log directory: {LOG_DIR}")
def launch_view_log():
    def log_selector(stdscr):
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        logs = sorted(LOG_DIR.glob("*.log"))
        selected = 0

        while True:
            stdscr.clear()
            stdscr.addstr(1, 2, "Select a log to view - ↑↓ to navigate, ENTER to open, Q to quit")

            for i, log_file in enumerate(logs):
                highlight = curses.color_pair(1) if i == selected else curses.A_NORMAL
                stdscr.addstr(3 + i, 4, log_file.name, highlight)

            stdscr.refresh()
            key = stdscr.getch()

            if key in [ord('q'), 27]: break
            elif key == curses.KEY_UP and selected > 0: selected -= 1
            elif key == curses.KEY_DOWN and selected < len(logs) - 1: selected += 1
            elif key in [curses.KEY_ENTER, ord('\n')]:
                viewer_script = f"""import os; os.system('cls' if os.name=='nt' else 'clear')
with open(r'{str(logs[selected])}') as f:
    print(f.read())
input("\\nPress Enter to exit...")"""
                temp = LOG_DIR / f"viewlog_{logs[selected].stem}.py"
                with open(temp, "w") as f: f.write(viewer_script)

                if platform.system() == "Windows":
                    subprocess.Popen(f'start cmd /c python "{temp}"', shell=True)
                else:
                    subprocess.Popen(["x-terminal-emulator", "-e", f"python3 {temp}"])

    curses.wrapper(log_selector)
def add_view_window():
    import sys
    import subprocess
    add_view_script = Path(__file__).parent / "launchlogview.py"
    interpreter = sys.executable
    # Launch in new terminal window per OS
    if sys.platform.startswith("win"):
        subprocess.Popen(["start", "cmd", "/c", interpreter, str(add_view_script)], shell=True)
    elif sys.platform.startswith("linux"):
        subprocess.Popen(["x-terminal-emulator", "-e", interpreter, str(add_view_script)])
    elif sys.platform == "darwin":
        subprocess.Popen(["osascript", "-e", f'tell app "Terminal" to do script "{interpreter} {add_view_script}"'])
    else:
        print("Unsupported platform for subprocess terminal execution.")