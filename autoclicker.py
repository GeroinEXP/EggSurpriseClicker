import tkinter as tk
from tkinter import ttk, scrolledtext
import win32gui
import win32con
import win32api
import time
import threading
import psutil
from pynput import keyboard
import json
import webbrowser
import os
import sys

class AutoClicker:
    def __init__(self, master):
        self.master = master
        master.title("Автокликер")
        master.geometry("400x600")

        self.window_list = self.get_window_list()
        self.is_running = False
        self.clicker_thread = None
        self.game_monitor_thread = None
        self.game_running = False

        self.config_file = "autoclicker_config.json"
        self.load_config()

        # Флаг для корректного завершения потоков
        self.should_stop = threading.Event()

        # Выбор приложения
        ttk.Label(master, text="Выберите приложение:").pack(pady=5)
        self.window_combo = ttk.Combobox(master, values=self.window_list)
        self.window_combo.pack(pady=5)
        self.window_combo.set(self.window_list[0] if self.window_list else "")

        # Настройка скорости кликов
        ttk.Label(master, text="Интервал между кликами (сек):").pack(pady=5)
        self.interval_entry = ttk.Entry(master)
        self.interval_entry.insert(0, "0.1")
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

        # Настройки для перезапуска игры
        ttk.Label(master, text="Steam App ID:").pack(pady=5)
        self.steam_app_id_entry = ttk.Entry(master)
        self.steam_app_id_entry.insert(0, "3017120")
        self.steam_app_id_entry.pack(pady=5)

        self.relaunch_var = tk.BooleanVar()
        self.relaunch_checkbox = ttk.Checkbutton(master, text="Перезапускать игру", variable=self.relaunch_var)
        self.relaunch_checkbox.pack(pady=5)

        # Кнопка запуска/остановки
        self.toggle_button = ttk.Button(master, text="Запустить (F5)", command=self.toggle_clicker_and_monitor)
        self.toggle_button.pack(pady=10)

        # Статус
        self.status_label = ttk.Label(master, text="Статус: Остановлен")
        self.status_label.pack(pady=5)

        # Текстовое поле для логов
        ttk.Label(master, text="Логи:").pack(pady=5)
        self.log_text = scrolledtext.ScrolledText(master, height=10)
        self.log_text.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)

        # Настройка слушателя клавиатуры
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

        # Заполнение полей сохраненными данными
        self.fill_saved_data()

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

        self.log(f"Запущен автокликер для {window_title}")
        while not self.should_stop.is_set():
            if not self.game_running:
                self.log("Игра не запущена. Ожидание...")
                if self.should_stop.wait(timeout=5):
                    break
                continue

            handle = self.get_window_handle(window_title)
            if not handle:
                self.log(f"Окно {window_title} не найдено. Ожидание...")
                if self.should_stop.wait(timeout=5):
                    break
                continue

            try:
                self.click(handle, x, y)
                if self.should_stop.wait(timeout=interval):
                    break
            except Exception as e:
                self.log(f"Ошибка при клике: {e}")
                if self.should_stop.wait(timeout=5):
                    break

        self.log("Автокликер остановлен")

    def monitor_and_relaunch_game(self):
        steam_app_id = self.steam_app_id_entry.get()
        self.log("Начало мониторинга игры")
        while not self.should_stop.is_set():
            if not self.is_game_running(steam_app_id):
                if self.game_running:
                    self.log(f"Игра (App ID: {steam_app_id}) закрылась. Попытка перезапуска.")
                else:
                    self.log(f"Игра (App ID: {steam_app_id}) не запущена. Попытка запуска.")
                self.game_running = False
                self.launch_steam_game(steam_app_id)
            else:
                if not self.game_running:
                    self.log(f"Игра (App ID: {steam_app_id}) успешно запущена.")
                    self.game_running = True
                    self.master.after(0, lambda: self.status_label.config(text="Статус: Игра запущена, кликер работает"))
            if self.should_stop.wait(timeout=5):
                break
        self.log("Мониторинг игры остановлен")

    def toggle_clicker_and_monitor(self):
        if self.is_running:
            self.stop_clicker_and_monitor()
        else:
            self.start_clicker_and_monitor()

    def start_clicker_and_monitor(self):
        self.should_stop.clear()
        self.is_running = True
        self.toggle_button.config(text=f"Остановить ({self.hotkey_entry.get()})")
        self.clicker_thread = threading.Thread(target=self.auto_clicker)
        self.clicker_thread.start()
        self.log("Автокликер запущен")
        if self.relaunch_var.get():
            self.game_monitor_thread = threading.Thread(target=self.monitor_and_relaunch_game)
            self.game_monitor_thread.start()
            self.log("Мониторинг игры запущен")
        self.status_label.config(text="Статус: Запущен")

    def stop_clicker_and_monitor(self):
        self.should_stop.set()
        self.is_running = False
        self.game_running = False
        self.toggle_button.config(text=f"Запустить ({self.hotkey_entry.get()})")
        self.log("Автокликер и мониторинг игры остановлены")
        self.status_label.config(text="Статус: Остановлен")

        # Ожидание завершения потоков
        if self.clicker_thread and self.clicker_thread.is_alive():
            self.clicker_thread.join(timeout=2)
        if self.game_monitor_thread and self.game_monitor_thread.is_alive():
            self.game_monitor_thread.join(timeout=2)

    def is_game_running(self, steam_app_id):
        for process in psutil.process_iter(['name', 'exe']):
            try:
                if process.name().lower() == f"steam_app_{steam_app_id}.exe" or \
                   (process.exe() and f"steamapps\\common" in process.exe().lower()):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def launch_steam_game(self, steam_app_id):
        self.log(f"Запуск игры через Steam URI (App ID: {steam_app_id})")
        webbrowser.open(f"steam://rungameid/{steam_app_id}")
        self.status_label.config(text=f"Статус: Запуск игры (App ID: {steam_app_id})")

    def on_press(self, key):
        if hasattr(key, 'char'):
            pressed_key = key.char
        elif hasattr(key, 'name'):
            pressed_key = key.name
        else:
            return

        if pressed_key.upper() == self.hotkey_entry.get().upper():
            self.master.after(0, self.toggle_clicker_and_monitor)

    def log(self, message):
        self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)

    def on_closing(self):
        self.log("Закрытие приложения...")
        self.stop_clicker_and_monitor()

        # Принудительное завершение потоков, если они все еще работают
        if self.clicker_thread and self.clicker_thread.is_alive():
            self.log("Принудительное завершение потока автокликера")
            self.clicker_thread._stop()
        if self.game_monitor_thread and self.game_monitor_thread.is_alive():
            self.log("Принудительное завершение потока мониторинга игры")
            self.game_monitor_thread._stop()

        self.listener.stop()
        self.log("Все потоки остановлены")
        self.save_config()
        self.master.destroy()
        sys.exit(0)  # Принудительно завершаем все потоки и процесс

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {}

    def save_config(self):
        self.config['steam_app_id'] = self.steam_app_id_entry.get()
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)

    def fill_saved_data(self):
        if 'steam_app_id' in self.config:
            self.steam_app_id_entry.delete(0, tk.END)
            self.steam_app_id_entry.insert(0, self.config['steam_app_id'])

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClicker(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()