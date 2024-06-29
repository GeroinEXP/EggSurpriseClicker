import tkinter as tk
from tkinter import ttk
import win32gui
import win32con
import win32api
import win32process
import time
import threading
import psutil
from pynput import keyboard

class AutoClicker:
    def __init__(self, master):
        self.master = master
        master.title("Автокликер")
        master.geometry("300x300")

        self.window_list = self.get_window_list()
        self.is_running = False
        self.clicker_thread = None

        # Выбор приложения
        ttk.Label(master, text="Выберите приложение:").pack(pady=5)
        self.window_combo = ttk.Combobox(master, values=self.window_list)
        self.window_combo.pack(pady=5)
        self.window_combo.set(self.window_list[0] if self.window_list else "")

        # Настройка скорости кликов
        ttk.Label(master, text="Интервал между кликами (сек):").pack(pady=5)
        self.interval_entry = ttk.Entry(master)
        self.interval_entry.insert(0, "1.0")
        self.interval_entry.pack(pady=5)

        # Координаты для клика
        ttk.Label(master, text="Координаты для клика (x, y):").pack(pady=5)
        coord_frame = ttk.Frame(master)
        coord_frame.pack(pady=5)
        self.x_entry = ttk.Entry(coord_frame, width=5)
        self.x_entry.insert(0, "100")
        self.x_entry.pack(side=tk.LEFT, padx=5)
        self.y_entry = ttk.Entry(coord_frame, width=5)
        self.y_entry.insert(0, "100")
        self.y_entry.pack(side=tk.LEFT, padx=5)

        # Настройка горячей клавиши
        ttk.Label(master, text="Горячая клавиша:").pack(pady=5)
        self.hotkey_entry = ttk.Entry(master)
        self.hotkey_entry.insert(0, "F5")
        self.hotkey_entry.pack(pady=5)

        # Кнопка запуска/остановки
        self.toggle_button = ttk.Button(master, text="Запустить (F5)", command=self.toggle_clicker)
        self.toggle_button.pack(pady=10)

        # Статус
        self.status_label = ttk.Label(master, text="Статус: Остановлен")
        self.status_label.pack(pady=5)

        # Настройка слушателя клавиатуры
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def get_window_list(self):
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                windows.append(win32gui.GetWindowText(hwnd))
        windows = []
        win32gui.EnumWindows(callback, windows)
        return sorted(set(windows))  # Удаляем дубликаты и сортируем

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
            self.status_label.config(text=f"Статус: Окно {window_title} не найдено")
            self.is_running = False
            return

        self.status_label.config(text=f"Статус: Запущен для {window_title}")
        while self.is_running:
            self.click(handle, x, y)
            time.sleep(interval)
        self.status_label.config(text="Статус: Остановлен")

    def toggle_clicker(self):
        if self.is_running:
            self.is_running = False
            self.toggle_button.config(text=f"Запустить ({self.hotkey_entry.get()})")
        else:
            self.is_running = True
            self.toggle_button.config(text=f"Остановить ({self.hotkey_entry.get()})")
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