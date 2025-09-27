import tkinter as tk
from tkinter import scrolledtext
import socket
import getpass
import os # модуль для работы с файловой системой
import argparse # модуль для разбора аргументов командной строки

class OSEmulator:
    def __init__(self, root, vfs_path=None, script_path=None):
        self.root = root # сохраняем ссылку на главное окно приложения
        self.root.title(f"Эмулятор - [{getpass.getuser()}@{socket.gethostname()}]") # получаем имя пользователя и hostname и устанавливаем их как заголовок
        self.root.geometry("800x500") # устанавливаем размеры
        self.root.minsize(800, 500) # устанавливаем минимальный размер окна

        self.vfs_path = vfs_path # сохраняем путь к виртуальной файловой системе
        self.script_path = script_path # сохраняем путь к стартовому скрипту

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

        # выводим информацию о параметрах запуска
        self.display_message("=== Параметр запуска ===\n")
        self.display_message(f"VFS путь: {vfs_path if vfs_path else 'не указан'}\n")
        self.display_message(f"Скрипт: {script_path if script_path else 'не указан'}\n")
        self.display_message("=======================\n\n")  # разделитель

        self.display_message("Добро пожаловать в эмулятор командной оболочки OC.\nВведите команду (например, ls, cd, exit).\n")

        # если указан скрипт, планируем его запуск через 100 мс после инициализации GUI
        if self.script_path:
            self.root.after(100, self.run_startup_script)  # after()


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

        self.display_message(f"{getpass.getuser()}@{socket.gethostname()}:~$ {command_input}\n") # выводим на экран введенную команду

        parts = command_input.split() # парсим по пробелам
        command = parts[0] # первый элемент списка - имя команды
        args = parts[1:] if len(parts) > 1 else [] # остальное - аргументы команды

        if command == "exit": # если введена команда exit, выходим из эмулятора
            self.root.quit()
            self.root.after(1000, self.root.quit) # завершаем программу через 1 секунду
        elif command == "ls": # если введена ls, выводим args через пробел
            self.display_message("Команда 'ls' вызвана c аргументами: " + " ".join(args) + "\n")
        elif command == "cd": # если введена cd, выводим args через пробел
            self.display_message("Команда 'cd' вызвана c аргументами: " + " ".join(args) + "\n")
        else: # иначе выводим сообщение об ошибке
            self.display_message(f"Ошибка: неизвестная команда '{command}'\n")


    def run_startup_script(self):
        if not self.script_path or not os.path.exists(self.script_path): # проверяем путь и существование файла
            self.display_message(f"Ошибка: скрипт '{self.script_path}' не найден\n")
            return

        self.display_message(f"\n=== Выполнение скрипта: {self.script_path} ===\n") # заголовок начала выполнения скрипта
        
        try: # обрабатываем ошибки
            with open(self.script_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            def execute_next_command(index=0): # рекурсивная функция для выполнения команд с задержкой
                if index >= len(lines):
                    self.display_message("=== Выполнение скрипта завершено ===\n\n")
                    return
                
                line = lines[index].strip() # получаем текущую строку без пробелов по краям
                
                if not line: # если строка пустая после удаления пробелов
                    self.root.after(100, execute_next_command, index + 1) # переходим к следующей строке через 100 мс
                    return
                
                if line.startswith('#'): # если строка начинается с символа комментария
                    self.display_message(f"# {line[1:]}\n")
                    self.root.after(100, execute_next_command, index + 1)
                    return
                
                self.display_message(f"{getpass.getuser()}@{socket.gethostname()} {line}\n")
                
                parts = line.split() # разделяем строку на части по пробелам
                command = parts[0] # первое слово команда
                args = parts[1:] if len(parts) > 1 else [] # остальные слова аргументы

                if command == "exit":
                    self.display_message("Завершение работы по скрипту...\n")
                    self.root.after(1000, self.root.quit) # завершаем программу через 1 секунду
                elif command == "ls":
                    self.display_message("Команда 'ls' вызвана c аргументами: " + " ".join(args) + "\n")
                    self.root.after(500, execute_next_command, index + 1)
                elif command == "cd":
                    self.display_message("Команда 'cd' вызвана c аргументами: " + " ".join(args) + "\n")
                    self.root.after(500, execute_next_command, index + 1)
                else:
                    self.display_message(f"Ошибка: неизвестная команда '{command}'\n")
                    self.root.after(500, execute_next_command, index + 1)

            execute_next_command() # начальный вызов рекурсивной функции
            
        except Exception as e: # перехват исключений
            self.display_message(f"Ошибка при выполнении скрипта: {str(e)}\n")


def parse_arguments():
    parser = argparse.ArgumentParser(description='Эмулятор командной оболочки OC') # создаем объект парсера
    parser.add_argument('--vfs', type=str, help='Путь к физическому расположению VFS') # добавляем параметр --vfs
    parser.add_argument('--script', type=str, help='Путь к стартовому скрипту') # добавляем параметр --script

    args = parser.parse_args() # парсим аргументы командной строки
    
    print("=== Аргументы командной строки ===")
    print(f"VFS путь: {args.vfs}")
    print(f"Скрипт: {args.script}")
    print("=================================")
    
    return args


if __name__ == "__main__":
    args = parse_arguments()

    root = tk.Tk() # создаем окно
    app = OSEmulator(root, vfs_path=args.vfs, script_path=args.script) # создаем экземпляр OSEmulator
    root.mainloop() # запускаем цикл обработки событий Tkinter