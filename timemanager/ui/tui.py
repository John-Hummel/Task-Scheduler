import curses
from datetime import datetime
from pathlib import Path 
import sys
base_path = Path(__file__).resolve().parent.parent
for folder in ["core", "ui"]:
    sys.path.append(str(base_path / folder))
print(f"Base path: {base_path}")
from config import load_config, config, save_config # type: ignore
from tasks import save_task  # type: ignore
from logger import log  # type: ignore
import os 
from taskmanager import launch_task_manager_window
from addtask import add_task_window 
from logview import add_view_window


def launch_tui():
    MENU_OPTIONS = ["Add Task", "Toggle Notify", "Task Manager", "View Log", "Exit"]

    def draw_menu(stdscr, selected_idx):
        stdscr.clear()
        stdscr.addstr(1, 2, "Main Menu - ↑↓ Navigate, ENTER Select, Q Quit")
        for i, label in enumerate(MENU_OPTIONS):
            prefix = "[>]" if i == selected_idx else "   "
            style = curses.color_pair(1) if i == selected_idx else curses.A_NORMAL
            stdscr.addstr(3 + i, 4, f"{prefix} {label}", style)
        stdscr.refresh()

    def main(stdscr):
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
        idx = 0

        while True:
            draw_menu(stdscr, idx)
            key = stdscr.getch()

            if key == curses.KEY_UP:
                idx = (idx - 1) % len(MENU_OPTIONS)
            elif key == curses.KEY_DOWN or key == 9:  # DOWN or TAB
                idx = (idx + 1) % len(MENU_OPTIONS)
            elif key in [curses.KEY_ENTER, 10, 13]:
                stdscr.clear()
                stdscr.refresh()
                curses.endwin()

                if idx == 0:
                    add_task_window()
                elif idx == 1:
                    config['notify'] = not config['notify']
                    save_config()
                    log("info", f"Notify setting toggled to: {config['notify']}")
                elif idx == 2:
                    launch_task_manager_window()
                elif idx == 3:
                    add_view_window()
                elif idx == 4:
                    break

                curses.doupdate()
                curses.reset_prog_mode()
                curses.curs_set(0)

    curses.wrapper(main)