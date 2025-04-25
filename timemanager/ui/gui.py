# === ui/gui.py ===
# Placeholder for GUI implementation
base_path = Path(__file__).resolve().parent.parent
for folder in ["core", "ui"]:
    sys.path.append(str(base_path / folder))
print(f"Base path: {base_path}")
import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
from tasks import save_task # type: ignore
from config import config # type: ignore

def launch_gui():
    def submit():
        name = name_var.get()
        dt = date_entry.get_date().strftime("%Y-%m-%d") + " " + time_var.get()
        is_exec = exec_var.get()
        exec_path = exec_path_var.get()

        if not name or not time_var.get():
            messagebox.showerror("Missing", "Task name and time required")
            return

        task = {
            "task_name": name,
            "datetime": dt,
            "task_type": "Executable" if is_exec else "Reminder",
            "exec_path": exec_path if is_exec else "",
            "recurrence": "None",
            "interval": 0
        }
        save_task(task)
        messagebox.showinfo("Saved", f"Task '{name}' scheduled.")
        root.destroy()

    root = tk.Tk()
    root.title("Schedule Task")

    tk.Label(root, text="Task Name:").grid(row=0, column=0)
    name_var = tk.StringVar()
    tk.Entry(root, textvariable=name_var).grid(row=0, column=1)

    tk.Label(root, text="Date:").grid(row=1, column=0)
    date_entry = DateEntry(root)
    date_entry.grid(row=1, column=1)

    tk.Label(root, text="Time (HH:MM):").grid(row=2, column=0)
    time_var = tk.StringVar()
    tk.Entry(root, textvariable=time_var).grid(row=2, column=1)

    exec_var = tk.BooleanVar()
    tk.Checkbutton(root, text="Executable Task?", variable=exec_var).grid(row=3, columnspan=2)

    tk.Label(root, text="Executable Path:").grid(row=4, column=0)
    exec_path_var = tk.StringVar()
    tk.Entry(root, textvariable=exec_path_var).grid(row=4, column=1)

    tk.Button(root, text="Submit", command=submit).grid(row=5, columnspan=2)

    root.mainloop()
