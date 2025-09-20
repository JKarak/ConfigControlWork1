
import tkinter as tk
from tkinter import scrolledtext
import socket
import getpass

class OSShellEmulator:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Эмулятор - [{getpass.getuser()}@{socket.gethostname()}]")
        self.root.geometry("800x600")

        # Создаем текстовое поле с прокруткой для вывода
        self.output_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='disabled')
        self.output_area.pack(expand=True, fill='both', padx=10, pady=10)

        # Создаем поле для ввода команды
        self.input_entry = tk.Entry(root, font=("Courier", 12))
        self.input_entry.pack(fill='x', padx=10, pady=5)
        self.input_entry.bind("<Return>", self.process_command)

        # Начальное приветствие
        self.display_message("Добро пожаловать в эмулятор командной оболочки ОС.\nВведите команду (например, ls, cd, exit).\n")

    def display_message(self, message):
        self.output_area.config(state='normal')
        self.output_area.insert(tk.END, message)
        self.output_area.see(tk.END)
        self.output_area.config(state='disabled')

    def process_command(self, event):
        command_input = self.input_entry.get().strip()
        self.input_entry.delete(0, tk.END)
        
        if not command_input:
            return

        # Выводим введенную команду
        self.display_message(f"$ {command_input}\n")

        # Простой парсер: разделяем на команду и аргументы по пробелам
        parts = command_input.split()
        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        # Обработка команд
        if command == "exit":
            self.display_message("Завершение работы эмулятора.\n")
            self.root.quit()
        elif command == "ls":
            self.display_message("Команда 'ls' вызвана с аргументами: " + " ".join(args) + "\n")
        elif command == "cd":
            self.display_message("Команда 'cd' вызвана с аргументами: " + " ".join(args) + "\n")
        else:
            self.display_message(f"Ошибка: неизвестная команда '{command}'\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = OSShellEmulator(root)
    root.mainloop()
