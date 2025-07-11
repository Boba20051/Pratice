import socket
import threading
import tkinter as tk
from tkinter import messagebox
import json
import time


class ChatClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Чат")
        self.root.geometry("400x200")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.nickname = ""
        self.client_socket = None
        self.connected = False
        self.server_ip = ""
        self.server_port = 0

        # Инициализация UI элементов
        self.nick_entry = None
        self.ip_entry = None
        self.port_entry = None
        self.user_listbox = None
        self.chat_text = None
        self.message_entry = None

        self.Login_menu()
        self.root.mainloop()

    def Login_menu(self):
        # Очищаем окно перед созданием элементов входа
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="Никнейм:").pack(pady=(10, 0))
        self.nick_entry = tk.Entry(self.root)
        self.nick_entry.pack(padx=20, pady=(0, 10), fill=tk.X)
        self.nick_entry.insert(0, "User")

        tk.Label(self.root, text="IP сервера:").pack()
        self.ip_entry = tk.Entry(self.root)
        self.ip_entry.pack(padx=20, pady=(0, 10), fill=tk.X)
        self.ip_entry.insert(0, "127.0.0.1")

        tk.Label(self.root, text="Порт сервера:").pack()
        self.port_entry = tk.Entry(self.root)
        self.port_entry.pack(padx=20, pady=(0, 10), fill=tk.X)
        self.port_entry.insert(0, "5555")

        self.connect_btn = tk.Button(self.root, text="Подключиться", command=self.on_connect)
        self.connect_btn.pack(pady=10)

    def setup_ui(self):
        self.root.geometry("800x600")
        # Очищаем окно перед созданием чата
        for widget in self.root.winfo_children():
            widget.destroy()

        # Сетка интерфейса
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Список пользователей
        self.user_frame = tk.Frame(self.root)
        self.user_frame.grid(row=0, column=1, sticky="ns", padx=5, pady=5)

        tk.Label(self.user_frame, text="Онлайн:").pack()
        self.user_listbox = tk.Listbox(self.user_frame, width=15)
        self.user_listbox.pack(fill="both", expand=True)

        # Чат
        self.chat_frame = tk.Frame(self.root)
        self.chat_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.chat_text = tk.Text(self.chat_frame, state="disabled")
        self.chat_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.chat_text.tag_config("system", foreground="gray")
        self.chat_text.tag_config("my_message", foreground="blue")
        self.chat_text.tag_config("other_message", foreground="black")

        self.input_frame = tk.Frame(self.chat_frame)
        self.input_frame.pack(fill="x", padx=5, pady=5)

        self.message_entry = tk.Entry(self.input_frame)
        self.message_entry.pack(side="left", fill="x", expand=True)
        self.message_entry.bind("<Return>", self.send_message)

        self.send_button = tk.Button(self.input_frame, text="Отправить", command=self.send_message)
        self.send_button.pack(side="right")

    def on_connect(self):
        self.nickname = self.nick_entry.get().strip()
        self.server_ip = self.ip_entry.get().strip()

        try:
            self.server_port = int(self.port_entry.get().strip())
        except ValueError:
            messagebox.showerror("Ошибка", "Порт должен быть числом")
            return

        if not self.nickname:
            messagebox.showerror("Ошибка", "Введите никнейм")
            return

        if not self.server_ip:
            messagebox.showerror("Ошибка", "Введите IP сервера")
            return

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_ip, self.server_port))
            self.client_socket.send(self.nickname.encode('utf-8'))
            self.connected = True

            # Переключаемся на интерфейс чата после успешного подключения
            self.setup_ui()
            threading.Thread(target=self.receive_messages, daemon=True).start()

            self.display_system_message(f"Подключено к серверу {self.server_ip}:{self.server_port}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться: {e}")

    def receive_messages(self):
        while self.connected:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    break

                data = json.loads(message)

                if data["type"] == "system":
                    self.display_system_message(data["text"])
                elif data["type"] == "message":
                    self.display_message(
                        data["from"],
                        data["text"],
                        data["time"],
                        is_me=(data["from"] == self.nickname),
                        is_history=data.get("is_history", False)
                    )
                elif data["type"] == "userlist":
                    self.update_user_list(data["users"])

            except json.JSONDecodeError:
                pass
            except Exception as e:
                self.display_system_message(f"Ошибка соединения: {e}")
                self.connected = False
                break

    def update_user_list(self, users):
        if self.user_listbox:  # Проверяем, что список пользователей инициализирован
            self.user_listbox.delete(0, "end")
            for user in users:
                if user:
                    self.user_listbox.insert("end", user)

    def display_system_message(self, text):
        if self.chat_text:  # Проверяем, что чат инициализирован
            self.chat_text.config(state="normal")
            self.chat_text.insert("end", f"⚡ {text}\n", "system")
            self.chat_text.config(state="disabled")
            self.chat_text.see("end")

    def display_message(self, sender, text, timestamp, is_me=True, is_history=False):
        if self.chat_text:  # Проверяем, что чат инициализирован
            self.chat_text.config(state="normal")
            if is_me:
                prefix = "Я"
                tag = "my_message"
            else:
                prefix = sender
                tag = "other_message"

            # Если сообщение из истории, делаем его немного бледнее
            if is_history:
                self.chat_text.tag_config("history_message", foreground="#888888")
                tag = "history_message"

            self.chat_text.insert(
                "end",
                f"[{timestamp}] {prefix}: {text}\n",
                tag
            )
            self.chat_text.config(state="disabled")
            self.chat_text.see("end")

    def send_message(self, event=None):
        if self.message_entry and self.connected:  # Проверяем, что поле ввода инициализировано
            message = self.message_entry.get()
            if message:
                try:
                    # Локальное отображение своего сообщения
                    self.display_message(
                        self.nickname,
                        message,
                        time.strftime("%H:%M:%S"),
                        is_me=True
                    )

                    # Отправка на сервер
                    self.client_socket.send(message.encode('utf-8'))
                    self.message_entry.delete(0, "end")
                except Exception as e:
                    self.display_system_message(f"Ошибка отправки: {e}")
                    self.connected = False

    def on_close(self):
        if self.connected:
            try:
                self.client_socket.close()
            except:
                pass
        self.root.destroy()


if __name__ == "__main__":
    client = ChatClient()