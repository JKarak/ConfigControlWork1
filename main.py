import tkinter as tk
from tkinter import scrolledtext
import socket
import getpass

class OSEmulator:
    def __init__(self, root):
        self.root = root # сохраняем ссылку на главное окно приложения
        self.root.title(f"Эмулятор - [{getpass.getuser()}@{socket.gethostname()}]") # получаем имя пользователя и hostname и устанавливаем их как заголовок
        self.root.geometry("900x500") # устанавливаем размеры

        self.output_area = scrolledtext.ScrolledText( # создаем текстовое поле с прокруткой для вывода
            root,
            wrap=tk.WORD, # перенос текста
            state='disabled' # блокируем пользователю возможность редактировать
        ) 
        self.output_area.pack(expand=True, fill='both', padx=10, pady=10) # заполняем виджетом все пространство, отступ 10

        self.input_entry = tk.Entry(
            root,
            font=("Courier", 12)
        )
        self.input_entry.pack(fill='x', padx=10, pady=5) # размещение поля и отступ
        self.input_entry.bind("<Return>", self.process_command) # привязываем обработчик нажатия Enter к функции process_command

        self.display_message("Добро пожаловать в эмулятор командной оболочки OC.\nВведите команду (например, ls, cd, exit).\n")


    def display_message(self, message): # метод для вывода на экран
        self.output_area.config(state='normal') # включаем режим редактирования поля
        self.output_area.insert(tk.END, message) # вставляем переданное сообщение в конец текстового поля
        self.output_area.see(tk.END) # автоматически прокручиваем текстовое поле к концу
        self.output_area.config(state='disabled') # блокируем режим редактирования поля


    def process_command(self, event): # метод для парсинга
        command_input = self.input_entry.get().strip() # получаем то что ввелось и обрезаем лишние пробелы
        self.input_entry.delete(0, tk.END) # очищаем поле ввода
        
        if not command_input: # если введеная строка пустая, то выходим из функции
            return

        self.display_message(f"{command_input}\n") # выводим на экран введенную команду

        parts = command_input.split() # парсим по пробелам
        command = parts[0] # первый элемент списка - имя команды
        args = parts[1:] if len(parts) > 1 else [] # остальное - аргументы команды

        if command == "exit": # если введена команда exit, выходим из эмулятора
            self.root.quit()
        elif command == "ls": # если введена ls, выводим args через пробел
            self.display_message("Команда 'ls' вызвана c аргументами: " + " ".join(args) + "\n")
        elif command == "cd": # если введена cd, выводим args через пробел
            self.display_message("Команда 'cd' вызвана c аргументами: " + " ".join(args) + "\n")
        else: # иначе выводим сообщение об ошибке
            self.display_message(f"Ошибка: неизвестная команда '{command}'\n")


if __name__ == "__main__":
    root = tk.Tk() # создаем окно
    app = OSEmulator(root) # создаем экземпляр OSEmulator
    root.mainloop() # запускаем цикл обработки событий Tkinter