# bootstrap.py
import os
import sys
import time
import subprocess
import threading
import platform
from pathlib import Path
from datetime import datetime

# === Optional: fallback logger if real logger not initialized ===
def log(level, msg):
    print(f"[{level.upper()}] {datetime.now().isoformat()} - {msg}")

# === CONFIG ===
WATCHDOG_INTERVAL = 5
DAEMON_SCRIPTS = {
    "scheduler": "daemons.py",
    "config": "config.py"
}
LOG_DIR = Path(__file__).resolve().parent / "bootlogs"
LOG_DIR.mkdir(exist_ok=True)

running_processes = {}

# === INSTALL MODULES ===
def install_required_modules():
    import importlib.util
    modules = ["pyfiglet", "plyer", "tkcalendar", "watchdog"]
    if platform.system() == "Windows":
        modules += ["windows-curses", "colorama", "pywin32"]

    for module in modules:
        try:
            __import__({
                "windows-curses": "curses",
                "pywin32": "win32api"
            }.get(module, module))
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", module])
            log("info", f"Installed missing module: {module}")

# === LOGGING STREAMS ===
def open_log_stream(name):
    stdout_path = LOG_DIR / f"{name}_stdout.log"
    stderr_path = LOG_DIR / f"{name}_stderr.log"
    stdout = open(stdout_path, "a")
    stderr = open(stderr_path, "a")
    return stdout, stderr

# === LAUNCH DAEMON ===
def launch_daemon(name, script):
    path = Path(__file__).resolve().parent / script
    if not path.exists():
        log("error", f"Daemon script not found: {path}")
        return

    log("info", f"Launching {name} in new console: {path}")
    interpreter = sys.executable

    if platform.system() == "Windows":
        subprocess.Popen(
            f'start "{name}_daemon" cmd /c "{interpreter} {path}"',
            shell=True
        )

    elif platform.system() == "Linux":
        # Try common terminal emulators (you can expand this)
        subprocess.Popen([
            "x-terminal-emulator", "-T", f"{name}_daemon", "-e", f"{interpreter} {path}"
        ])
    elif platform.system() == "Darwin":
        # macOS AppleScript terminal launch
        subprocess.Popen([
            "osascript", "-e",
            f'tell app "Terminal" to do script "{interpreter} {path}"'
        ])
    else:
        # Fallback to inline subprocess with logging
        stdout, stderr = open_log_stream(name)
        proc = subprocess.Popen([interpreter, str(path)], stdout=stdout, stderr=stderr)
        running_processes[name] = {"process": proc, "stdout": stdout, "stderr": stderr}
        log("info", f"Started {name} inline (no console fork)")


# === MONITOR & RESTART ===
def monitor_daemons():
    while True:
        for name, info in list(running_processes.items()):
            proc = info["process"]
            if proc.poll() is not None:
                log("warning", f"{name} crashed. Restarting...")
                info["stdout"].close()
                info["stderr"].close()
                launch_daemon(name, DAEMON_SCRIPTS[name])
        time.sleep(WATCHDOG_INTERVAL)

# === MAIN ===
def run_bootstrap():
    install_required_modules()

    for name, script in DAEMON_SCRIPTS.items():
        print(f"Launching {name} daemon...")

        launch_daemon(name, script)

    threading.Thread(target=monitor_daemons, daemon=True).start()
    log("info", "Daemon watchdog launched")

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        log("info", "Graceful shutdown requested")
        for name, info in running_processes.items():
            proc = info["process"]
            proc.terminate()
            info["stdout"].close()
            info["stderr"].close()
        log("info", "All daemons terminated")
        sys.exit(0)

if __name__ == "__main__":
    interpreter = sys.executable
    subprocess.Popen(
            f'start "watcher_daemon" cmd /k "{interpreter} core\\bootstraplauncher.py"',
            shell=True
        )
