import tkinter as tk
from tkinter import scrolledtext
import socket
import getpass
import os
import argparse
import json
import base64

class OSEmulator:
    def __init__(self, root, vfs_path=None, script_path=None):
        self.root = root  # сохраняем ссылку на главное окно приложения
        self.root.title(f"Эмулятор - [{getpass.getuser()}@{socket.gethostname()}]")  # получаем имя пользователя и hostname и устанавливаем их как заголовок
        self.root.geometry("800x500")  # устанавливаем размеры
        self.root.minsize(800, 500)  # устанавливаем минимальный размер окна

        self.vfs_path = vfs_path  # сохраняем путь к виртуальной файловой системе
        self.script_path = script_path  # сохраняем путь к стартовому скрипту
        self.vfs_data = None  # хранилище данных VFS
        self.current_path = "/"  # текущий путь в VFS

        self.output_area = scrolledtext.ScrolledText(  # создаем текстовое поле с прокруткой для вывода
            root,
            wrap=tk.WORD,  # перенос текста
            state='disabled'  # блокируем пользователю возможность редактировать
        ) 
        self.output_area.pack(expand=True, fill='both', padx=10, pady=10)  # заполняем виджетом все пространство, отступ 10

        self.input_entry = tk.Entry(  # создаем поле для ввода команд
            root,
            font=("Courier", 12)  # устанавливаем шрифт для поля ввода
        )
        self.input_entry.pack(fill='x', padx=10, pady=5)  # размещение поля и отступ
        self.input_entry.bind("<Return>", self.process_command)  # привязываем обработчик нажатия Enter к функции process_command

        # выводим информацию о параметрах запуска
        self.display_message("=== Параметры запуска ===\n")
        self.display_message(f"VFS путь: {vfs_path if vfs_path else 'не указан'}\n")
        self.display_message(f"Скрипт: {script_path if script_path else 'не указан'}\n")
        self.display_message("=======================\n\n")

        if self.vfs_path:  # если указан путь к VFS, загружаем ее
            self.load_vfs()

        self.display_message("Добро пожаловать в эмулятор командной оболочки OC.\nВведите команду (например, ls, cd, pwd, cat).\nВведите exit для выхода. Для получения информации о командах, введите help.")

        # если указан скрипт, планируем его запуск через 100 мс после инициализации GUI
        if self.script_path:
            self.root.after(100, self.run_startup_script)  # after()

    def load_vfs(self):
        # загрузка VFS из JSON файла
        try:
            if not os.path.exists(self.vfs_path):  # проверяем существование файла VFS
                self.display_message(f"Ошибка: VFS файл '{self.vfs_path}' не найден\n")
                return
            
            with open(self.vfs_path, 'r', encoding='utf-8') as f:  # открываем файл VFS для чтения
                self.vfs_data = json.load(f)  # загружаем JSON данные
            
            self.display_message(f"VFS успешно загружена из '{self.vfs_path}'\n")
            
            # Проверяем наличие motd и выводим его
            self.display_motd()
            
        except json.JSONDecodeError as e:  # обработка ошибок формата JSON
            self.display_message(f"Ошибка загрузки VFS: неверный формат JSON - {str(e)}\n")
        except Exception as e:  # обработка других ошибок
            self.display_message(f"Ошибка загрузки VFS: {str(e)}\n")

    def display_motd(self):
        # вывод сообщения motd если оно существует в VFS
        if self.vfs_data and 'files' in self.vfs_data:  # проверяем наличие раздела files в VFS
            for file_entry in self.vfs_data['files']:  # перебираем все файлы в VFS
                if file_entry.get('name') == 'motd' and file_entry.get('type') == 'file':  # ищем файл motd
                    content = file_entry.get('content', '')  # получаем содержимое файла
                    if file_entry.get('encoding') == 'base64':  # проверяем кодировку base64
                        try:
                            content = base64.b64decode(content).decode('utf-8')  # декодируем из base64
                        except Exception as e:
                            self.display_message(f"Ошибка декодирования motd: {str(e)}\n")
                            return
                    
                    self.display_message(f"\n=== MOTD ===\n{content}\n============\n\n")  # выводим motd
                    return  # Выходим после нахождения первого motd

    def find_in_vfs(self, path):
        """Поиск файла или папки в VFS по пути"""
        if not self.vfs_data or 'files' not in self.vfs_data:  # проверяем загружена ли VFS
            return None
        
        # Нормализуем путь
        if not path.startswith('/'):  # если путь относительный
            # Для относительных путей добавляем текущий путь
            if self.current_path == '/':
                full_path = '/' + path
            else:
                full_path = self.current_path + '/' + path
        else:
            full_path = path
            
        full_path = os.path.normpath(full_path).replace('\\', '/')  # нормализуем путь
        
        # Ищем точное совпадение пути
        for entry in self.vfs_data['files']:  # перебираем все записи в VFS
            entry_path = entry.get('path', '')
            if entry_path == full_path:  # сравниваем пути
                return entry
        
        return None

    def list_directory(self, path):
        """Получение списка файлов и папок в указанном пути"""
        if not self.vfs_data or 'files' not in self.vfs_data:  # проверяем загружена ли VFS
            return []
        
        # Нормализуем путь
        if not path.startswith('/'):  # если путь относительный
            if self.current_path == '/':
                target_path = '/' + path
            else:
                target_path = self.current_path + '/' + path
        else:
            target_path = path
            
        target_path = os.path.normpath(target_path).replace('\\', '/')  # нормализуем путь
        if target_path != '/':  # добавляем слеш в конец для папок
            target_path = target_path + '/'
        
        items = []  # список элементов в папке
        seen_items = set()  # множество для отслеживания дубликатов
        
        for entry in self.vfs_data['files']:  # перебираем все записи в VFS
            entry_path = entry.get('path', '')  # получаем путь записи
            
            # Проверяем, находится ли запись в целевой папке
            if entry_path.startswith(target_path):  # проверяем вхождение в нужную папку
                # Получаем относительный путь от целевой папки
                relative_path = entry_path[len(target_path):]
                
                if '/' in relative_path:  # если это вложенная структура
                    # Это вложенный элемент - берем первую часть как папку
                    folder_name = relative_path.split('/')[0]  # получаем имя первой папки
                    if folder_name and folder_name not in seen_items:  # проверяем дубликаты
                        items.append({
                            'name': folder_name,
                            'type': 'directory'  # отмечаем как папку
                        })
                        seen_items.add(folder_name)  # добавляем в множество просмотренных
                else:
                    # Это непосредственный элемент в целевой папке
                    if relative_path and relative_path not in seen_items:  # проверяем дубликаты
                        items.append({
                            'name': relative_path,
                            'type': entry.get('type', 'file')  # сохраняем тип из записи
                        })
                        seen_items.add(relative_path)  # добавляем в множество просмотренных
        
        return sorted(items, key=lambda x: (x['type'] != 'directory', x['name']))  # сортируем: сначала папки, потом файлы

    def resolve_path(self, target_path):
        """Разрешение пути относительно текущего местоположения"""
        if target_path.startswith('/'):  # если путь абсолютный
            return os.path.normpath(target_path).replace('\\', '/')  # просто нормализуем
        else:  # если путь относительный
            if self.current_path == '/':  # если текущий путь - корень
                new_path = '/' + target_path
            else:
                new_path = self.current_path + '/' + target_path
            return os.path.normpath(new_path).replace('\\', '/')  # нормализуем и возвращаем

    def path_exists(self, path):
        """Проверка существования пути в VFS"""
        if not self.vfs_data or 'files' not in self.vfs_data:  # проверяем загружена ли VFS
            return False
        
        # Корень всегда существует
        if path == '/':
            return True
            
        # Проверяем точное совпадение пути
        for entry in self.vfs_data['files']:  # перебираем все записи в VFS
            entry_path = entry.get('path', '')
            if entry_path == path:  # точное совпадение пути
                return True
                
            # Для папок проверяем, есть ли файлы внутри этой папки
            if entry_path.startswith(path + '/'):  # путь начинается с указанного пути
                return True
                
        return False  # путь не найден

    def display_message(self, message):  # метод для вывода на экран
        self.output_area.config(state='normal')  # включаем режим редактирования поля
        self.output_area.insert(tk.END, message)  # вставляем переданное сообщение в конец текстового поля
        self.output_area.see(tk.END)  # автоматически прокручиваем текстовое поле к концу
        self.output_area.config(state='disabled')  # блокируем режим редактирования поля

    def process_command(self, event):  # метод для парсинга
        command_input = self.input_entry.get().strip()  # получаем то что ввелось и обрезаем лишние пробелы
        self.input_entry.delete(0, tk.END)  # очищаем поле ввода
        
        if not command_input:  # если введеная строка пустая, то выходим из функции
            return

        self.display_message(f"{getpass.getuser()}@{socket.gethostname()}:{self.current_path}$ {command_input}\n")  # выводим на экран введенную команду

        parts = command_input.split()  # парсим по пробелам
        command = parts[0]  # первый элемент списка - имя команды
        args = parts[1:] if len(parts) > 1 else []  # остальное - аргументы команды

        if command == "exit":  # если введена команда exit, выходим из эмулятора
            self.root.quit()
        elif command == "ls":  # если введена ls
            target_path = args[0] if args else self.current_path  # определяем целевой путь
            items = self.list_directory(target_path)  # получаем список элементов
            
            if items is None:  # проверяем на ошибку
                self.display_message(f"Ошибка: путь '{target_path}' не найден в VFS\n")
            else:
                if not items:  # если папка пустая
                    self.display_message("Папка пуста\n")
                else:
                    for item in items:  # перебираем все элементы
                        item_type = "d" if item['type'] == 'directory' else "-"  # определяем тип
                        self.display_message(f"{item_type} {item['name']}\n")  # выводим информацию
        elif command == "cd":  # если введена cd
            if not args:  # если аргументов нет
                self.current_path = "/"  # переходим в корень
                self.display_message("Переход в корневую папку\n")
            else:
                target_path = args[0]  # берем первый аргумент как целевой путь
                new_path = self.resolve_path(target_path)  # вычисляем новый путь
                
                if self.path_exists(new_path):  # проверяем существование пути в VFS
                    self.current_path = new_path  # обновляем текущий путь
                    self.display_message(f"Текущий путь: {self.current_path}\n")
                else:
                    self.display_message(f"Ошибка: путь '{target_path}' не найден в VFS\n")
        elif command == "cat":  # если введена cat
            if not args:  # проверяем наличие аргументов
                self.display_message("Ошибка: укажите имя файла\n")
            else:
                filename = args[0]  # берем имя файла
                file_entry = self.find_in_vfs(filename)  # ищем файл в VFS
                
                if file_entry and file_entry.get('type') == 'file':  # проверяем что это файл
                    content = file_entry.get('content', '')  # получаем содержимое
                    if file_entry.get('encoding') == 'base64':  # проверяем кодировку
                        try:
                            content = base64.b64decode(content).decode('utf-8')  # декодируем base64
                        except Exception as e:
                            self.display_message(f"Ошибка декодирования файла: {str(e)}\n")
                            return
                    
                    self.display_message(f"Содержимое файла '{filename}':\n{content}\n")  # выводим содержимое
                else:
                    self.display_message(f"Ошибка: файл '{filename}' не найден\n")
        elif command == "pwd":  # если введена pwd
            self.display_message(f"Текущий путь: {self.current_path}\n")  # выводим текущий путь
        elif command == "help":  # если введена help
            self.display_message("Доступные команды:\n")
            self.display_message("  ls [path]     - список файлов и папок\n")
            self.display_message("  cd [path]     - сменить текущую папку\n")
            self.display_message("  cat <file>    - показать содержимое файла\n")
            self.display_message("  pwd           - показать текущий путь\n")
            self.display_message("  exit          - выход из эмулятора\n")
            self.display_message("  help          - эта справка\n")
        else:  # иначе выводим сообщение об ошибке
            self.display_message(f"Ошибка: неизвестная команда '{command}'\n")

    def run_startup_script(self):
        if not self.script_path or not os.path.exists(self.script_path):  # проверяем путь и существование файла
            self.display_message(f"Ошибка: скрипт '{self.script_path}' не найден\n")
            return

        self.display_message(f"\n=== Выполнение скрипта: {self.script_path} ===\n")  # заголовок начала выполнения скрипта
        
        try:  # обрабатываем ошибки
            with open(self.script_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            def execute_next_command(index=0):  # рекурсивная функция для выполнения команд с задержкой
                if index >= len(lines):
                    self.display_message("=== Выполнение скрипта завершено ===\n\n")
                    return
                
                line = lines[index].strip()  # получаем текущую строку без пробелов по краям
                
                if not line:  # если строка пустая после удаления пробелов
                    self.root.after(100, execute_next_command, index + 1)  # переходим к следующей строке через 100 мс
                    return
                
                if line.startswith('#'):  # если строка начинается с символа комментария
                    self.display_message(f"# {line[1:]}\n")
                    self.root.after(100, execute_next_command, index + 1)
                    return
                
                self.display_message(f"{getpass.getuser()}@{socket.gethostname()}:{self.current_path}$ {line}\n")
                
                parts = line.split()  # разделяем строку на части по пробелам
                command = parts[0]  # первое слово команда
                args = parts[1:] if len(parts) > 1 else []  # остальные слова аргументы

                if command == "exit":
                    self.display_message("Завершение работы по скрипту...\n")
                    self.root.after(1000, self.root.quit)  # завершаем программу через 1 секунду
                elif command == "ls":
                    target_path = args[0] if args else self.current_path  # определяем целевой путь
                    items = self.list_directory(target_path)  # получаем список элементов
                    
                    if items is None:  # проверяем на ошибку
                        self.display_message(f"Ошибка: путь '{target_path}' не найден в VFS\n")
                    else:
                        if not items:  # если папка пустая
                            self.display_message("Папка пуста\n")
                        else:
                            for item in items:  # перебираем все элементы
                                item_type = "d" if item['type'] == 'directory' else "-"  # определяем тип
                                self.display_message(f"{item_type} {item['name']}\n")  # выводим информацию
                    self.root.after(500, execute_next_command, index + 1)
                elif command == "cd":
                    if not args:  # если аргументов нет
                        self.current_path = "/"  # переходим в корень
                        self.display_message("Переход в корневую папку\n")
                    else:
                        target_path = args[0]  # берем первый аргумент как целевой путь
                        new_path = self.resolve_path(target_path)  # вычисляем новый путь
                        
                        if self.path_exists(new_path):  # проверяем существование пути в VFS
                            self.current_path = new_path  # обновляем текущий путь
                            self.display_message(f"Текущий путь: {self.current_path}\n")
                        else:
                            self.display_message(f"Ошибка: путь '{target_path}' не найден в VFS\n")
                    self.root.after(500, execute_next_command, index + 1)
                elif command == "cat":
                    if not args:  # проверяем наличие аргументов
                        self.display_message("Ошибка: укажите имя файла\n")
                    else:
                        filename = args[0]  # берем имя файла
                        file_entry = self.find_in_vfs(filename)  # ищем файл в VFS
                        
                        if file_entry and file_entry.get('type') == 'file':  # проверяем что это файл
                            content = file_entry.get('content', '')  # получаем содержимое
                            if file_entry.get('encoding') == 'base64':  # проверяем кодировку
                                try:
                                    content = base64.b64decode(content).decode('utf-8')  # декодируем base64
                                except Exception as e:
                                    self.display_message(f"Ошибка декодирования файла: {str(e)}\n")
                                    self.root.after(500, execute_next_command, index + 1)
                                    return
                            
                            self.display_message(f"Содержимое файла '{filename}':\n{content}\n")  # выводим содержимое
                        else:
                            self.display_message(f"Ошибка: файл '{filename}' не найден\n")
                    self.root.after(500, execute_next_command, index + 1)
                elif command == "pwd":
                    self.display_message(f"Текущий путь: {self.current_path}\n")  # выводим текущий путь
                    self.root.after(500, execute_next_command, index + 1)
                elif command == "help":
                    self.display_message("Доступные команды:\n")
                    self.display_message("  ls [path]     - список файлов и папок\n")
                    self.display_message("  cd [path]     - сменить текущую папку\n")
                    self.display_message("  cat <file>    - показать содержимое файла\n")
                    self.display_message("  pwd           - показать текущий путь\n")
                    self.display_message("  exit          - выход из эмулятора\n")
                    self.display_message("  help          - эта справка\n")
                    self.root.after(500, execute_next_command, index + 1)
                else:
                    self.display_message(f"Ошибка: неизвестная команда '{command}'\n")
                    self.root.after(500, execute_next_command, index + 1)

            execute_next_command()  # начальный вызов рекурсивной функции
            
        except Exception as e:  # перехват исключений
            self.display_message(f"Ошибка при выполнении скрипта: {str(e)}\n")


def parse_arguments():
    parser = argparse.ArgumentParser(description='Эмулятор командной оболочки OC')  # создаем объект парсера
    parser.add_argument('--vfs', type=str, help='Путь к файлу VFS в формате JSON')  # добавляем параметр --vfs
    parser.add_argument('--script', type=str, help='Путь к стартовому скрипту')  # добавляем параметр --script

    args = parser.parse_args()  # парсим аргументы командной строки
    
    print("=== Аргументы командной строки ===")
    print(f"VFS путь: {args.vfs}")
    print(f"Скрипт: {args.script}")
    print("=================================")
    
    return args


if __name__ == "__main__":
    args = parse_arguments()

    root = tk.Tk()  # создаем окно
    app = OSEmulator(root, vfs_path=args.vfs, script_path=args.script)  # создаем экземпляр OSEmulator
    root.mainloop()  # запускаем цикл обработки событий Tkinter