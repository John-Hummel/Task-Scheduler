# === BOOTSTRAPPER ===
import sys
import os
import subprocess
import platform
import importlib.util
from colorama import Fore, Style, init
init(autoreset=True)

# Initial soft check for required modules
soft_required_modules = ["tkcalendar", "pyfiglet", "plyer", "tkinter"]
missing_modules = []

for module in soft_required_modules:
    if importlib.util.find_spec(module) is None:
        missing_modules.append(module)

if missing_modules:
    print(f"{Fore.YELLOW}[BOOTSTRAP WARNING]{Style.RESET_ALL} Missing modules detected: {', '.join(missing_modules)}")
    print(f"{Fore.YELLOW}  → Some features may not work as expected. Consider installing the missing modules.{Style.RESET_ALL}")
else:
    print(f"{Fore.GREEN}[BOOTSTRAP]{Style.RESET_ALL} All soft-required modules are available.")

# === MODULE INSTALLATION ===
def install_required_modules():
    required_modules = ["tkcalendar", "pyfiglet", "plyer"]
    if platform.system() == "Windows":
        required_modules.append("win32com")
        required_modules.append("curses")  # Add windows-curses for Windows

    for module in required_modules:
        try:
            __import__(module)
            print(f"{Fore.GREEN}[BOOTSTRAP]{Style.RESET_ALL} {module} is available.")
        except ImportError:
            print(f"{Fore.YELLOW}[BOOTSTRAP]{Style.RESET_ALL} Installing missing module: {module}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", module])

    # Soft check for tkinter
    try:
        import tkinter
        print(f"{Fore.GREEN}[BOOTSTRAP]{Style.RESET_ALL} tkinter is available.")
    except ImportError:
        print(f"{Fore.YELLOW}[BOOTSTRAP WARNING]{Style.RESET_ALL} 'tkinter' is not installed.")
        print(f"{Fore.YELLOW}  → GUI features will not work.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}  → On Debian/Ubuntu: sudo apt install python3-tk{Style.RESET_ALL}")

    # Soft check for required modules
    soft_required_modules = ["tkcalendar", "pyfiglet", "plyer", "tkinter"]
    for module in soft_required_modules:
        try:
            __import__(module)
            print(f"{Fore.GREEN}[BOOTSTRAP]{Style.RESET_ALL} {module} is available.")
        except ImportError:
            print(f"{Fore.YELLOW}[BOOTSTRAP WARNING]{Style.RESET_ALL} '{module}' is not installed.")
            if module == "tkinter":
                print(f"{Fore.YELLOW}  → GUI features will not work.{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}  → On Debian/Ubuntu: sudo apt install python3-tk{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}  → Some features may not work as expected. Consider installing '{module}'.{Style.RESET_ALL}")

    # Relaunch script if modules were installed
    if not all_modules_installed(required_modules):
        if "--restarted" not in sys.argv:  # Prevent infinite restart loop
            print(f"{Fore.RED}[BOOTSTRAP]{Style.RESET_ALL} Relaunching script to finalize module installation...")
            os.execv(sys.executable, [sys.executable] + sys.argv + ["--restarted"])
        else:
            print(f"{Fore.RED}[BOOTSTRAP ERROR]{Style.RESET_ALL} Module installation failed or incomplete. Exiting.")
            sys.exit(1)
    else:
        print(f"{Fore.GREEN}[BOOTSTRAP]{Style.RESET_ALL} All required modules are installed.")

def all_modules_installed(modules):
    for module in modules:
        if module == "pywin32":
            if importlib.util.find_spec("win32com") is None:
                return False
        elif importlib.util.find_spec(module) is None:
            return False
    return True

install_required_modules()

import json
import time
import uuid
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox
from tkcalendar import DateEntry
from pyfiglet import Figlet
from datetime import datetime, timedelta
from plyer import notification
# === INITIALIZATION ===
def setup_autostart():
    script_path = os.path.abspath(__file__)
    system = platform.system()

    if system == "Windows":
        startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
        shortcut_path = os.path.join(startup_folder, "TaskScheduler.lnk")
        if not os.path.exists(shortcut_path):
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = f'"{script_path}"'
            shortcut.WorkingDirectory = os.path.dirname(script_path)
            shortcut.IconLocation = script_path
            shortcut.save()

    elif system == "Linux":
        autostart_dir = os.path.expanduser("~/.config/autostart")
        os.makedirs(autostart_dir, exist_ok=True)
        desktop_entry = f"""[Desktop Entry]
Type=Application
Exec=python3 "{script_path}"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Task Scheduler
Comment=Start Task Scheduler on login
"""
        with open(os.path.join(autostart_dir, "task_scheduler.desktop"), "w") as f:
            f.write(desktop_entry)

    elif system == "Darwin":
        plist = f"""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.taskscheduler</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
        plist_path = os.path.expanduser("~/Library/LaunchAgents/com.user.taskscheduler.plist")
        with open(plist_path, "w") as f:
            f.write(plist)

# === GLOBAL VARIABLES ===
CONFIG_FILE = "config.json"
TASKS_FILE = "tasks.json"
tasks, task_types, exec_paths, recurring, custom_intervals = {}, {}, {}, {}, {}
config = {
    "ascii": True,
    "notify": True,
    "default_seconds": 5,
    "autostart": False,
    "silent": False
}

# === CONFIGURATION ===
def load_config():
    global config
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config.update(json.load(f))
            print(f"{Fore.GREEN}[CONFIG]{Style.RESET_ALL} Configuration loaded successfully.")
    except Exception as e:
        print(f"{Fore.RED}[CONFIG ERROR]{Style.RESET_ALL} Error loading config: {e}")

def save_config():
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"{Fore.GREEN}[CONFIG]{Style.RESET_ALL} Configuration saved successfully.")
    except Exception as e:
        print(f"{Fore.RED}[CONFIG ERROR]{Style.RESET_ALL} Error saving config: {e}")

# === TASK PERSISTENCE ===
def save_tasks():
    try:
        with open(TASKS_FILE, 'w') as f:
            json.dump({
                'tasks': tasks,
                'types': task_types,
                'exec_paths': exec_paths,
                'recurring': recurring,
                'custom_intervals': custom_intervals
            }, f)
        print(f"{Fore.GREEN}[TASKS]{Style.RESET_ALL} Tasks saved successfully.")
    except Exception as e:
        print(f"{Fore.RED}[TASKS ERROR]{Style.RESET_ALL} Error saving tasks: {e}")

def load_tasks():
    try:
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, 'r') as f:
                data = json.load(f)
                tasks.update(data.get('tasks', {}))
                task_types.update(data.get('types', {}))
                exec_paths.update(data.get('exec_paths', {}))
                recurring.update(data.get('recurring', {}))
                custom_intervals.update(data.get('custom_intervals', {}))
            print(f"{Fore.GREEN}[TASKS]{Style.RESET_ALL} Tasks loaded successfully.")
    except Exception as e:
        print(f"{Fore.RED}[TASKS ERROR]{Style.RESET_ALL} Error loading tasks: {e}")

# === TASK MANAGEMENT ===
def add_task(data):
    task_name = data["task_name"]
    task_datetime = data["datetime"]
    recurrence = data["recurrence"]
    interval = data["interval"]
    exec_path = data["exec_path"]
    task_type = data["task_type"]

    if task_name in tasks:
        messagebox.showerror("Error", f"Task '{task_name}' already exists.")
        return

    tasks[task_name] = task_datetime.strftime("%Y-%m-%d %H:%M")
    task_types[task_name] = 'executable' if task_type == "Executable" else 'reminder'

    if task_type == "Executable":
        exec_paths[task_name] = exec_path

    if recurrence != "None":
        recurring[task_name] = recurrence
    if recurrence == "Custom" and interval > 0:
        custom_intervals[task_name] = interval

    save_tasks()
    print(f"[TASKS] Task '{task_name}' scheduled for {task_datetime} with recurrence: {recurrence}.")

def remove_task(task_name):
    if task_name in tasks:
        tasks.pop(task_name, None)
        task_types.pop(task_name, None)
        exec_paths.pop(task_name, None)
        recurring.pop(task_name, None)
        custom_intervals.pop(task_name, None)
        save_tasks()
        print(f"{Fore.GREEN}[TASKS]{Style.RESET_ALL} Task '{task_name}' has been removed.")
    else:
        print(f"{Fore.RED}[TASKS]{Style.RESET_ALL} Task '{task_name}' not found.")

# === SCHEDULER ===
def run_scheduler():
    if not config.get("silent"):
        print("Scheduler is now running...\n\n")
    while True:
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M")
        for name in list(tasks):
            if tasks[name] == now_str:
                handle_task_execution(name)
        time.sleep(30)

def handle_task_execution(task_name):
    if task_types.get(task_name) == 'executable':
        launch_exec_countdown(task_name, exec_paths.get(task_name, ""))
    else:
        launch_reminder_countdown(task_name)

    if task_name in recurring:
        next_time = get_next_occurrence(datetime.now(), recurring[task_name], task_name)
        if next_time:
            tasks[task_name] = next_time.strftime("%Y-%m-%d %H:%M")
        else:
            remove_task(task_name)
    else:
        remove_task(task_name)

# === GUI SCHEDULER INPUT ===
def select_task_info():
    result = {}

    def submit():
        task_type = task_type_var.get()
        task_name = task_name_var.get()
        task_time = time_var.get()
        task_date = date_entry.get_date()
        recurrence = recurrence_var.get()
        interval = interval_var.get()
        exec_path = exec_path_var.get()

        if not task_name or not task_time:
            messagebox.showerror("Error", "Task name and time are required.")
            return

        if task_type == "Executable" and not exec_path:
            messagebox.showerror("Error", "Executable path is required for executable tasks.")
            return

        try:
            result.update({
                "task_type": task_type,
                "task_name": task_name,
                "datetime": datetime.strptime(f"{task_date} {task_time}", "%Y-%m-%d %H:%M"),
                "recurrence": recurrence,
                "interval": int(interval) if interval else 0,
                "exec_path": exec_path
            })
            dialog.destroy()
        except ValueError:
            messagebox.showerror("Error", "Invalid time format or interval.")

    dialog = tk.Tk()
    dialog.title("Schedule Task")

    tk.Label(dialog, text="Task Type:").grid(row=0, column=0)
    task_type_var = tk.StringVar(value="Reminder")
    tk.OptionMenu(dialog, task_type_var, "Reminder", "Executable").grid(row=0, column=1)

    tk.Label(dialog, text="Task Name:").grid(row=1, column=0)
    task_name_var = tk.StringVar()
    tk.Entry(dialog, textvariable=task_name_var).grid(row=1, column=1)

    tk.Label(dialog, text="Date:").grid(row=2, column=0)
    date_entry = DateEntry(dialog)
    date_entry.grid(row=2, column=1)

    tk.Label(dialog, text="Time (HH:MM):").grid(row=3, column=0)
    time_var = tk.StringVar(value="12:00")
    tk.Entry(dialog, textvariable=time_var).grid(row=3, column=1)

    tk.Label(dialog, text="Recurrence:").grid(row=4, column=0)
    recurrence_var = tk.StringVar(value="None")
    tk.OptionMenu(dialog, recurrence_var, "None", "Daily", "Weekly", "Monthly", "Yearly", "Custom").grid(row=4, column=1)

    tk.Label(dialog, text="Custom Interval (minutes):").grid(row=5, column=0)
    interval_var = tk.StringVar(value="0")
    tk.Entry(dialog, textvariable=interval_var).grid(row=5, column=1)

    tk.Label(dialog, text="Executable Path:").grid(row=6, column=0)
    exec_path_var = tk.StringVar()
    tk.Entry(dialog, textvariable=exec_path_var).grid(row=6, column=1)

    tk.Button(dialog, text="Schedule", command=submit).grid(row=7, columnspan=2)
    dialog.mainloop()

    return result

def add_task_unified():
    data = select_task_info()
    if not data:
        return

    task_name = data["task_name"]
    task_datetime = data["datetime"]
    recurrence = data["recurrence"]
    interval = data["interval"]
    exec_path = data["exec_path"]
    task_type = data["task_type"]

    if task_name in tasks:
        messagebox.showerror("Error", f"Task '{task_name}' already exists.")
        return

    tasks[task_name] = task_datetime.strftime("%Y-%m-%d %H:%M")
    task_types[task_name] = 'executable' if task_type == "Executable" else 'reminder'

    if task_type == "Executable":
        exec_paths[task_name] = exec_path

    if recurrence != "None":
        recurring[task_name] = recurrence
    if recurrence == "Custom" and interval > 0:
        custom_intervals[task_name] = interval

    save_tasks()
    print(f"[TASKS] Task '{task_name}' scheduled for {task_datetime} with recurrence: {recurrence}.")

    if not task_name or not exec_path or not task_datetime:
        messagebox.showerror("Error", "All fields are required.")
        return

    try:
        parsed_time = task_datetime
        tasks[task_name] = parsed_time.strftime("%Y-%m-%d %H:%M")
        task_types[task_name] = 'executable'
        exec_paths[task_name] = exec_path
        if recurrence != "None":
            recurring[task_name] = recurrence
        if recurrence == "Custom" and interval > 0:
            custom_intervals[task_name] = interval
        save_tasks()
        print(f"Executable task '{task_name}' scheduled for {parsed_time} with recurrence: {recurrence}.")
    except ValueError:
        messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD HH:MM.")

def get_next_occurrence(current_time, recurrence, task_name=None):
    if recurrence == "Daily":
        return current_time + timedelta(days=1)
    elif recurrence == "Weekly":
        return current_time + timedelta(weeks=1)
    elif recurrence == "Monthly":
        try:
            next_month = current_time.replace(day=1) + timedelta(days=32)
            return next_month.replace(day=current_time.day)
        except ValueError:
            return None
    elif recurrence == "Yearly":
        try:
            return current_time.replace(year=current_time.year + 1)
        except ValueError:
            return None
    elif recurrence == "Custom" and task_name in custom_intervals:
        return current_time + timedelta(minutes=custom_intervals[task_name])
    return None

def run_scheduler():
    if not config.get("silent"):
        print("Scheduler is now running...\n\n")
    while True:
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M")
        for name in list(tasks):
            if tasks[name] == now_str:
                if task_types.get(name) == 'executable':
                    launch_exec_countdown(name, exec_paths.get(name, ""))
                else:
                    launch_reminder_countdown(name)
                if name in recurring:
                    next_time = get_next_occurrence(now, recurring[name], name)
                    if next_time:
                        tasks[name] = next_time.strftime("%Y-%m-%d %H:%M")
                    else:
                        del tasks[name]
                        task_types.pop(name, None)
                        exec_paths.pop(name, None)
                        recurring.pop(name, None)
                        custom_intervals.pop(name, None)
                else:
                    del tasks[name]
                    task_types.pop(name, None)
                    exec_paths.pop(name, None)
                    recurring.pop(name, None)
                    custom_intervals.pop(name, None)
                save_tasks()
        time.sleep(30)

def list_tasks():
    if not tasks:
        print(f"{Fore.YELLOW}[TASKS]{Style.RESET_ALL} No tasks scheduled.")
    else:
        print(f"{Fore.CYAN}[TASKS]{Style.RESET_ALL} Scheduled tasks:")
        for name, time_str in tasks.items():
            t_type = task_types.get(name, "reminder")
            recurrence = recurring.get(name, "None")
            interval = custom_intervals.get(name, 0)
            interval_str = f" | Interval: {interval} min" if recurrence == "Custom" else ""
            print(f"{Fore.GREEN}- {name}{Style.RESET_ALL} ({t_type}) → {time_str} | Recurs: {recurrence}{interval_str}")

# === TASK MANAGEMENT HELPERS ===
def remove_task_interactive():
    if not tasks:
        print("[INFO] No tasks available to remove.")
        return

    print("\n[SELECT TASK TO REMOVE]")
    task_list = list(tasks.keys())
    for idx, task in enumerate(task_list, 1):
        print(f"{idx}. {task} ({task_types.get(task, 'reminder')})")

    try:
        selection = int(input("Enter the number of the task to remove: "))
        if 1 <= selection <= len(task_list):
            selected_task = task_list[selection - 1]
            remove_task(selected_task)
        else:
            print("[WARN] Invalid selection.")
    except ValueError:
        print("[WARN] Invalid input. Please enter a number.")

# === ASCII COUNTDOWN TOOLS ===
def launch_exec_countdown(task_name, exec_path):
    if not config.get("ascii"):
        try:
            subprocess.run(exec_path, shell=True)
        except Exception as e:
            print(f"Execution error: {e}")
        return

    script = f'''import os, time, platform, subprocess
from pyfiglet import Figlet

def countdown():
    fig = Figlet(font='slant')
    for i in range({config['default_seconds']}, 0, -1):
        os.system('cls' if platform.system() == 'Windows' else 'clear')
        print(fig.renderText(f"{task_name}{{i}}s left"))
        time.sleep(1)
    subprocess.run({repr(exec_path)}, shell=True)

    time.sleep(3)
    os.remove(os.path.abspath(__file__))

countdown()'''
    temp = f"exec_debug_{uuid.uuid4().hex[:6]}.py"
    with open(temp, 'w') as f: f.write(script)
    if platform.system() == "Windows":
        subprocess.Popen(f'start cmd /c python {temp}', shell=True)
    elif platform.system() == "Linux":
        subprocess.Popen(["x-terminal-emulator", "-e", f"python3 {temp}"])
    elif platform.system() == "Darwin":
        subprocess.Popen(["osascript", "-e", f'tell app "Terminal" to do script "python3 {temp}"'])
    else:
        print("Unsupported OS for terminal launch.")

def launch_reminder_countdown(task_name):
    if not config.get("ascii"):
        if config.get("notify"):
            notification.notify(title="Reminder", message=f"Time to do: {task_name}", timeout=5)
        return

    script = f'''import os, time, platform
from pyfiglet import Figlet
from plyer import notification

def countdown():
    fig = Figlet(font='slant')
    for i in range({config['default_seconds']}, 0, -1):
        os.system('cls' if platform.system() == 'Windows' else 'clear')
        print(fig.renderText(f"{task_name}\\n{{i}}s left"))
        time.sleep(1)
    notification.notify(title="Reminder", message=f"Time to do: {task_name}", timeout=5)
    time.sleep(3)
    try:
        os.remove(os.path.abspath(__file__))
    except:
        pass

countdown()'''

    temp = f"reminder_debug_{uuid.uuid4().hex[:6]}.py"
    with open(temp, 'w') as f: f.write(script)
    if platform.system() == "Windows":
        subprocess.Popen(f'start cmd /c python {temp}', shell=True)
    elif platform.system() == "Linux":
        subprocess.Popen(["x-terminal-emulator", "-e", f"python3 {temp}"])
    elif platform.system() == "Darwin":
        subprocess.Popen(["osascript", "-e", f'tell app \"Terminal\" to do script \"python3 {temp}\""'])
    else:
        print("Unsupported OS for terminal launch.")
import curses
import os
import json
from datetime import datetime

MENU_OPTIONS = [
    "Add Task (Reminder or Executable)",
    "Edit Config",
    "View Tasks",
    "View Log",
    "Exit"
]

LOG_FILE = "task_scheduler.log"
TASKS_FILE = "tasks.json"
config = {
    "use_tui_input": False
}
tasks = []


def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")


def save_task(task):
    global tasks
    tasks.append(task)
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, default=str, indent=4)


def load_tasks():
    global tasks
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as f:
            tasks = json.load(f)


load_tasks()

def tui_datetime_prompt():
    def input_scroll_menu(stdscr):
        curses.curs_set(0)
        stdscr.keypad(True)
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

        now = datetime.now()
        year, month, day, hour, minute = now.year, now.month, now.day, now.hour, now.minute
        field_idx = 0
        fields = ["Year", "Month", "Day", "Hour", "Minute"]

        while True:
            stdscr.clear()
            stdscr.addstr(1, 2, "Scroll with arrows. TAB to switch. Enter to confirm.")
            stdscr.addstr(2, 2, f"Selected: {year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}")

            for i, label in enumerate(fields):
                val = [year, month, day, hour, minute][i]
                highlight = curses.color_pair(1) if i == field_idx else curses.A_NORMAL
                stdscr.addstr(4 + i, 4, f"[{'>' if i == field_idx else ' '}] {label}: {val}", highlight)
            stdscr.refresh()

            key = stdscr.getch()

            if key == curses.KEY_UP:
                if field_idx == 0:
                    year += 1
                elif field_idx == 1:
                    month = 1 if month == 12 else month + 1
                elif field_idx == 2:
                    day = 1 if day >= 31 else day + 1
                elif field_idx == 3:
                    hour = (hour + 1) % 24
                elif field_idx == 4:
                    minute = (minute + 1) % 60
            elif key == curses.KEY_DOWN:
                if field_idx == 0:
                    year -= 1
                elif field_idx == 1:
                    month = 12 if month == 1 else month - 1
                elif field_idx == 2:
                    day = 31 if day <= 1 else day - 1
                elif field_idx == 3:
                    hour = (hour - 1) % 24
                elif field_idx == 4:
                    minute = (minute - 1) % 60
            elif key == 9:  # TAB
                field_idx = (field_idx + 1) % len(fields)
            elif key in [curses.KEY_ENTER, ord('\n')]:
                try:
                    dt = datetime(year, month, day, hour, minute)
                    return dt
                except ValueError:
                    stdscr.addstr(10, 2, "Invalid date. Try again.")
                    stdscr.refresh()
                    stdscr.getch()
            elif key in [27, ord('q')]:
                return None

    return curses.wrapper(input_scroll_menu)


def tui_task_input():
    def task_form(stdscr):
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)

        name = ""
        is_exec = False
        recurrence = "None"
        interval = 0
        exec_path = ""
        step = 0

        while True:
            stdscr.clear()
            stdscr.addstr(1, 2, "Task Creator - TAB to navigate, Enter to edit/toggle")

            highlights = [curses.color_pair(1) if step == i else curses.A_NORMAL for i in range(5)]
            stdscr.addstr(3, 4, f"[{'>' if step == 0 else ' '}] Task Name: {name}", highlights[0])
            stdscr.addstr(4, 4, f"[{'>' if step == 1 else ' '}] Executable?: {is_exec}", highlights[1])
            stdscr.addstr(5, 4, f"[{'>' if step == 2 else ' '}] Exec Path: {exec_path if is_exec else '(N/A)'}", highlights[2])
            stdscr.addstr(6, 4, f"[{'>' if step == 3 else ' '}] Recurrence: {recurrence}", highlights[3])
            stdscr.addstr(7, 4, f"[{'>' if step == 4 else ' '}] Interval (min): {interval}", highlights[4])

            stdscr.addstr(9, 2, "Press 'd' to pick datetime, 's' to save, 'q' to quit")
            stdscr.refresh()
            key = stdscr.getch()

            if key == ord('q'):
                break
            elif key == 9:  # TAB
                step = (step + 1) % 5
            elif key in [curses.KEY_ENTER, ord('\n')]:
                curses.echo()
                if step == 0:
                    stdscr.addstr(11, 4, "Enter Task Name: ")
                    name = stdscr.getstr(11, 25, 30).decode("utf-8")
                elif step == 1:
                    is_exec = not is_exec
                elif step == 2 and is_exec:
                    stdscr.addstr(11, 4, "Enter Executable Path: ")
                    exec_path = stdscr.getstr(11, 29, 50).decode("utf-8")
                elif step == 3:
                    stdscr.addstr(11, 4, "Recurrence (None/Daily/...): ")
                    recurrence = stdscr.getstr(11, 32, 20).decode("utf-8")
                elif step == 4:
                    stdscr.addstr(11, 4, "Custom Interval in min: ")
                    try:
                        interval = int(stdscr.getstr(11, 29, 5).decode("utf-8"))
                    except:
                        interval = 0
                curses.noecho()
            elif key == ord('d'):
                dt = tui_datetime_prompt()
                if dt:
                    task_data = {
                        "task_name": name,
                        "task_type": "Executable" if is_exec else "Reminder",
                        "exec_path": exec_path if is_exec else "",
                        "recurrence": recurrence,
                        "interval": interval,
                        "datetime": dt.strftime("%Y-%m-%d %H:%M")
                    }
                    save_task(task_data)
                    log(f"Task added: {task_data}")
                    stdscr.addstr(14, 2, "Task saved. Press any key to return.", curses.color_pair(2))
                    stdscr.getch()
                    break

    curses.wrapper(task_form)


def tui_view_tasks():
    def task_view(stdscr):
        curses.curs_set(0)
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        stdscr.addstr(1, 2, "Scheduled Tasks:")

        if not tasks:
            stdscr.addstr(3, 2, "No tasks available.")
        else:
            for i, (task_name, task_time) in enumerate(tasks.items()):
                highlight = curses.A_REVERSE if i % 2 == 0 else curses.A_NORMAL
                stdscr.addstr(3 + i, 4, f"{i+1}. {task_name} - {task_time}", highlight)

        stdscr.addstr(h - 2, 2, "Press any key to return.")
        stdscr.refresh()
        stdscr.getch()

    curses.wrapper(task_view)

def tui_main_menu():
    def draw_menu(stdscr, selected_idx, task_idx, config_idx, offset_task, offset_config, mode):
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        title = "ASCII Task Scheduler"
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(1, (w - len(title)) // 2, title)
        stdscr.attroff(curses.color_pair(2))

        if mode == "menu" or mode == "task":
            stdscr.addstr(3, 2, "Main Menu:")
            for idx, option in enumerate(MENU_OPTIONS):
                row = 4 + idx
                if row < h - 2:
                    prefix = "> " if idx == selected_idx and mode == "menu" else "  "
                    stdscr.attron(curses.color_pair(1) if idx == selected_idx and mode == "menu" else curses.A_NORMAL)
                    stdscr.addstr(row, 4, prefix + option[:w - 6])
                    stdscr.attroff(curses.color_pair(1) if idx == selected_idx and mode == "menu" else curses.A_NORMAL)

        elif mode == "config":
            stdscr.addstr(3, 2, "Config:")
            config_list = list(config.items())[offset_config:offset_config + h - 6]
            for i, (k, v) in enumerate(config_list):
                row = 4 + i
                if row < h - 2:
                    prefix = "> " if i + offset_config == config_idx else "  "
                    line = f"{k}: {v}"[:w - 6]
                    stdscr.attron(curses.color_pair(1) if i + offset_config == config_idx else curses.A_NORMAL)
                    stdscr.addstr(row, 4, prefix + line)
                    stdscr.attroff(curses.color_pair(1) if i + offset_config == config_idx else curses.A_NORMAL)

        legend = "TAB=Switch ↑↓=Nav ENTER=Select q/ESC=Back"
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(h - 1, 2, legend[:w - 4])
        stdscr.attroff(curses.color_pair(2))
        stdscr.refresh()

    def prompt_yes_no(stdscr, question):
        h, w = stdscr.getmaxyx()
        stdscr.clear()
        stdscr.addstr(h//2 - 1, (w - len(question)) // 2, question[:w-2])
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(h//2 + 1, w//2 - 6, "[ Yes ]")
        stdscr.attroff(curses.color_pair(3))
        stdscr.attron(curses.color_pair(4))
        stdscr.addstr(h//2 + 1, w//2 + 2, "[ No ]")
        stdscr.attroff(curses.color_pair(4))
        stdscr.refresh()
        while True:
            key = stdscr.getch()
            if key in [ord('y'), ord('Y'), ord('\n')]:
                return True
            elif key in [ord('n'), ord('N'), 27]:
                return False

    def prompt_new_value(stdscr, key, current):
        curses.echo()
        stdscr.clear()
        stdscr.addstr(2, 2, f"Enter new value for '{key}' (current: {current}): ")
        stdscr.refresh()
        new_val = stdscr.getstr(3, 2).decode("utf-8")
        curses.noecho()
        return new_val

    def view_log(stdscr):
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        stdscr.addstr(1, 2, "Log Viewer (press any key to return)")
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                lines = f.readlines()[-(h - 4):]
                for i, line in enumerate(lines):
                    stdscr.addstr(i + 3, 2, line[:w - 4])
        else:
            stdscr.addstr(3, 2, "No log file found.")
        stdscr.refresh()
        stdscr.getch()

    def main(stdscr):
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_RED)

        selected_idx = 0
        config_idx = 0
        offset_config = 0
        mode = "menu"

        while True:
            draw_menu(stdscr, selected_idx, 0, config_idx, 0, offset_config, mode)
            key = stdscr.getch()
            if mode == "menu":
                if key == curses.KEY_UP and selected_idx > 0:
                    selected_idx -= 1
                elif key == curses.KEY_DOWN and selected_idx < len(MENU_OPTIONS) - 1:
                    selected_idx += 1
                elif key in [curses.KEY_ENTER, ord("\n")]:
                    if selected_idx == 0:
                        if config.get("use_tui_input"):
                            tui_task_input()
                        else:
                            dt = tui_datetime_prompt()
                            if dt:
                                log(f"Selected datetime: {dt}")
                    elif selected_idx == 1:
                        mode = "config"
                    elif selected_idx == 2:
                        tui_view_tasks()
                    elif selected_idx == 3:
                        view_log(stdscr)
                    elif selected_idx == 4:
                        if prompt_yes_no(stdscr, "Are you sure you want to exit?"):
                            break
                elif key == 9:
                    mode = "config"

            elif mode == "config":
                config_keys = list(config.keys())
                if key == curses.KEY_UP and config_idx > 0:
                    config_idx -= 1
                elif key == curses.KEY_DOWN and config_idx < len(config_keys) - 1:
                    config_idx += 1
                elif key in [curses.KEY_ENTER, ord("\n")]:
                    k = config_keys[config_idx]
                    if isinstance(config[k], bool):
                        config[k] = not config[k]
                    elif isinstance(config[k], int):
                        try:
                            val = int(prompt_new_value(stdscr, k, config[k]))
                            config[k] = val
                        except ValueError:
                            pass
                    log(f"Config '{k}' updated to {config[k]}")
                elif key in [27, ord('q'), 9]:
                    mode = "menu"

    curses.wrapper(main)

def edit_config():
    print("\nCurrent Config:")
    for k, v in config.items():
        print(f"- {k}: {v}")
    key = input("Enter setting to change (or blank to cancel): ")
    if key in config:
        val = input(f"Enter new value for '{key}' (current: {config[key]}): ")
        if val.lower() in ["true", "false"]:
            config[key] = val.lower() == "true"
        elif val.isdigit():
            config[key] = int(val)
        else:
            config[key] = val
        save_config()
        print(f"Updated config: {key} = {config[key]}")

# === MAIN INTERFACE ===
if __name__ == "__main__":
    load_config()
    load_tasks()
    if config.get("autostart"):
        setup_autostart()

    if config.get("silent"):
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        while True:
            time.sleep(60)
    else:
        print("Task Scheduler is starting...")
        print("Press Ctrl+C to stop the scheduler.")
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()

        try:
            tui_main_menu()
        except KeyboardInterrupt:
            print("\nExiting Task Scheduler.")