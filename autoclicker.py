import tkinter as tk
from tkinter import ttk
import win32gui
import win32con
import win32api
import time
import threading
from pynput import keyboard

class AutoClicker:
    def __init__(self, master):
        self.master = master
        master.title("Autoclicker/Автокликер")
        master.geometry("350x350")

        self.languages = {
            "English": {
                "select_app": "Select application:",
                "interval": "Click interval (sec):",
                "coordinates": "Click coordinates (x, y):",
                "hotkey": "Hotkey:",
                "start": "Start",
                "stop": "Stop",
                "status": "Status: Stopped",
                "running": "Status: Running for",
                "not_found": "Status: Window not found",
                "stopped": "Status: Stopped"
            },
            "Русский": {
                "select_app": "Выберите приложение:",
                "interval": "Интервал между кликами (сек):",
                "coordinates": "Координаты для клика (x, y):",
                "hotkey": "Горячая клавиша:",
                "start": "Запустить",
                "stop": "Остановить",
                "status": "Статус: Остановлен",
                "running": "Статус: Запущен для",
                "not_found": "Статус: Окно не найдено",
                "stopped": "Статус: Остановлен"
            }
        }

        self.current_language = "English"
        self.window_list = self.get_window_list()
        self.is_running = False
        self.clicker_thread = None

        # Language selection
        ttk.Label(master, text="Language / Язык:").pack(pady=5)
        self.lang_combo = ttk.Combobox(master, values=list(self.languages.keys()))
        self.lang_combo.set(self.current_language)
        self.lang_combo.pack(pady=5)
        self.lang_combo.bind("<<ComboboxSelected>>", self.change_language)

        # Application selection
        self.app_label = ttk.Label(master, text=self.languages[self.current_language]["select_app"])
        self.app_label.pack(pady=5)
        self.window_combo = ttk.Combobox(master, values=self.window_list)
        self.window_combo.pack(pady=5)
        self.window_combo.set(self.window_list[0] if self.window_list else "")

        # Click interval
        self.interval_label = ttk.Label(master, text=self.languages[self.current_language]["interval"])
        self.interval_label.pack(pady=5)
        self.interval_entry = ttk.Entry(master)
        self.interval_entry.insert(0, "1.0")
        self.interval_entry.pack(pady=5)

        # Click coordinates
        self.coord_label = ttk.Label(master, text=self.languages[self.current_language]["coordinates"])
        self.coord_label.pack(pady=5)
        coord_frame = ttk.Frame(master)
        coord_frame.pack(pady=5)
        self.x_entry = ttk.Entry(coord_frame, width=5)
        self.x_entry.insert(0, "100")
        self.x_entry.pack(side=tk.LEFT, padx=5)
        self.y_entry = ttk.Entry(coord_frame, width=5)
        self.y_entry.insert(0, "100")
        self.y_entry.pack(side=tk.LEFT, padx=5)

        # Hotkey setup
        self.hotkey_label = ttk.Label(master, text=self.languages[self.current_language]["hotkey"])
        self.hotkey_label.pack(pady=5)
        self.hotkey_entry = ttk.Entry(master)
        self.hotkey_entry.insert(0, "F5")
        self.hotkey_entry.pack(pady=5)

        # Start/Stop button
        self.toggle_button = ttk.Button(master, text=self.languages[self.current_language]["start"], command=self.toggle_clicker)
        self.toggle_button.pack(pady=10)

        # Status
        self.status_label = ttk.Label(master, text=self.languages[self.current_language]["status"])
        self.status_label.pack(pady=5)

        # Keyboard listener setup
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def change_language(self, event):
        self.current_language = self.lang_combo.get()
        self.app_label.config(text=self.languages[self.current_language]["select_app"])
        self.interval_label.config(text=self.languages[self.current_language]["interval"])
        self.coord_label.config(text=self.languages[self.current_language]["coordinates"])
        self.hotkey_label.config(text=self.languages[self.current_language]["hotkey"])
        self.toggle_button.config(text=self.languages[self.current_language]["start"])
        self.status_label.config(text=self.languages[self.current_language]["status"])

    def get_window_list(self):
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                windows.append(win32gui.GetWindowText(hwnd))
        windows = []
        win32gui.EnumWindows(callback, windows)
        return sorted(set(windows))

    def get_window_handle(self, window_title):
        return win32gui.FindWindow(None, window_title)

    def click(self, handle, x, y):
        lParam = win32api.MAKELONG(x, y)
        win32gui.PostMessage(handle, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
        win32gui.PostMessage(handle, win32con.WM_LBUTTONUP, None, lParam)

    def auto_clicker(self):
        window_title = self.window_combo.get()
        x = int(self.x_entry.get())
        y = int(self.y_entry.get())
        interval = float(self.interval_entry.get())

        handle = self.get_window_handle(window_title)
        if not handle:
            self.status_label.config(text=self.languages[self.current_language]["not_found"])
            self.is_running = False
            return

        self.status_label.config(text=f"{self.languages[self.current_language]['running']} {window_title}")
        while self.is_running:
            self.click(handle, x, y)
            time.sleep(interval)
        self.status_label.config(text=self.languages[self.current_language]["stopped"])

    def toggle_clicker(self):
        if self.is_running:
            self.is_running = False
            self.toggle_button.config(text=self.languages[self.current_language]["start"])
        else:
            self.is_running = True
            self.toggle_button.config(text=self.languages[self.current_language]["stop"])
            self.clicker_thread = threading.Thread(target=self.auto_clicker)
            self.clicker_thread.start()

    def on_press(self, key):
        if hasattr(key, 'char'):
            pressed_key = key.char
        elif hasattr(key, 'name'):
            pressed_key = key.name
        else:
            return

        if pressed_key.upper() == self.hotkey_entry.get().upper():
            self.master.after(0, self.toggle_clicker)

    def on_closing(self):
        self.is_running = False
        if self.clicker_thread:
            self.clicker_thread.join()
        self.listener.stop()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClicker(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()