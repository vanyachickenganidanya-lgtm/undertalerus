import os
import json
import subprocess
import requests
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QLineEdit, QPushButton)
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtCore import Qt, QThread, Signal

# 1. НАСТРОЙКА КЛИЕНТА (OpenRouter)
API_KEY = "ТВОЙ_OPENROUTER_API_KEY"  # <-- Сюда свой ключ
URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "google/gemini-3.5-flash"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost",
    "X-Title": "Gemini+ OS Agent Qt"
}

# 2. ФУНКЦИИ ИНСТРУМЕНТОВ (Остались без изменений)
def get_file(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f"--- Содержимое {path} ---\n{f.read()}"
    except Exception as e: return f"Ошибка чтения файла: {str(e)}"

def create_file(path, filename):
    try:
        full_path = os.path.join(path, filename)
        with open(full_path, "w", encoding="utf-8") as f: f.write("")
        return f"Успех: Файл создан по пути {full_path}"
    except Exception as e: return f"Ошибка создания файла: {str(e)}"

def write_file(path, content):
    try:
        with open(path, "a", encoding="utf-8") as f: f.write(content + "\n")
        return f"Успех: Данные записаны в {path}"
    except Exception as e: return f"Ошибка записи: {str(e)}"

def get_files(folder_path):
    try:
        if os.path.exists(folder_path):
            return f"Файлы в {folder_path}:\n" + "\n".join(os.listdir(folder_path))
        return "Ошибка: Указанная папка не существует."
    except Exception as e: return f"Ошибка получения списка: {str(e)}"

def run_cmd(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30, encoding="cp866")
        return f"Команда выполнена. Вывод:\n{result.stdout if result.stdout else result.stderr}"
    except Exception as e: return f"Ошибка терминала: {str(e)}"

def run_python(code):
    try:
        result = subprocess.run(["python", "-c", code], capture_output=True, text=True, timeout=15)
        return f"Вывод Python:\n{result.stdout if result.stdout else result.stderr}"
    except Exception as e: return f"Ошибка Python: {str(e)}"

def run_cpp(code, exe_name="temp_ai_app"):
    try:
        cpp_file = f"{exe_name}.cpp"
        with open(cpp_file, "w", encoding="utf-8") as f: f.write(code)
        compile_res = subprocess.run(["g++", cpp_file, "-o", exe_name], capture_output=True, text=True)
        if compile_res.returncode != 0: return f"❌ Ошибка компиляции g++:\n{compile_res.stderr}"
        
        run_res = subprocess.run([f"./{exe_name}" if os.name != 'nt' else f"{exe_name}.exe"], capture_output=True, text=True)
        if os.path.exists(cpp_file): os.remove(cpp_file)
        if os.path.exists(f"{exe_name}.exe"): os.remove(f"{exe_name}.exe")
        return f"🚀 Успешный запуск C++!\nВывод программы:\n{run_res.stdout}"
    except Exception as e: return f"Ошибка среды C++: {str(e)}"

tools_map = {
    "get_file": get_file, "create_file": create_file, "write_file": write_file,
    "get_files": get_files, "run_cmd": run_cmd, "run_python": run_python, "run_cpp": run_cpp
}

tools_definition = [
    {"type": "function", "function": {"name": "get_file", "description": "Аналог get.file(место). Читает файл.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "create_file", "description": "Аналог create.file(место, название). Создает пустой файл.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "filename": {"type": "string"}}, "required": ["path", "filename"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Аналог write.file(место, что написать). Пишет текст в файл.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "get_files", "description": "Аналог get.files(место папки). Показывает список файлов.", "parameters": {"type": "object", "properties": {"folder_path": {"type": "string"}}, "required": ["folder_path"]}}},
    {"type": "function", "function": {"name": "run_cmd", "description": "Запускает любые команды в консоли (cmd/bash/pacman).", "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "run_python", "description": "Выполняет чистый скрипт на Python и возвращает вывод.", "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}},
    {"type": "function", "function": {"name": "run_cpp", "description": "Принимает исходный код C++, компилирует его через g++ и запускает.", "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}}
]

# 3. АСИНХРОННЫЙ ПОТОК ДЛЯ СЕТЕВЫХ ЗАПРОСОВ (Чтобы GUI не фризило)
class NetworkWorker(QThread):
    result_signal = Signal(str)

    def __init__(self, user_text):
        super().__init__()
        self.user_text = user_text

    def run(self):
        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": f"Ты системный помощник. Выполни задачу пользователя, используя подходящий инструмент: {self.user_text}"}],
            "tools": tools_definition,
            "tool_choice": "auto"
        }
        try:
            response = requests.post(URL, headers=headers, data=json.dumps(payload), timeout=60)
            if response.status_code != 200:
                self.result_signal.emit(f"❌ Ошибка сервера OpenRouter ({response.status_code}): {response.text}\n")
                return

            message = response.json()['choices'][0]['message']

            if 'tool_calls' in message and message['tool_calls']:
                output_buffer = ""
                for call in message['tool_calls']:
                    f_name = call['function']['name']
                    args = json.loads(call['function']['arguments'])
                    output_buffer += f"🤖 [Вызов {f_name}] с аргументами: {args}\n"
                    
                    if f_name in tools_map:
                        res = tools_map[f_name](**args)
                        output_buffer += f"{res}\n"
                self.result_signal.emit(output_buffer)
            else:
                self.result_signal.emit(f"🤖 ИИ: {message.get('content', '')}\n")
        except Exception as e:
            self.result_signal.emit(f"❌ Ошибка выполнения: {str(e)}\n")

# 4. ГЛАВНОЕ ОКНО НА PYSIDE6
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gemini+ Ultimate OS Agent (PySide6)")
        self.resize(750, 550)

        # Стилизация под Dark Mode
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e2e; }
            QTextEdit { background-color: #252538; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; }
            QLineEdit { background-color: #252538; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 6px; }
            QPushButton { background-color: #89b4fa; color: #11111b; font-weight: bold; border-radius: 6px; padding: 6px; }
            QPushButton:hover { background-color: #b4befe; }
        """)

        # Виджеты
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setFont(QFont("Consolas", 11))
        self.chat_history.append("Система: Агент PySide6 запущен и готов к работе.\n")
        main_layout.addWidget(self.chat_history)

        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Прикажи мне что-нибудь...")
        self.input_field.returnPressed.connect(self.send_command)
        input_layout.addWidget(self.input_field, stretch=4)

        self.send_btn = QPushButton("Выполнить")
        self.send_btn.clicked.connect(self.send_command)
        input_layout.addWidget(self.send_btn, stretch=1)

        main_layout.addLayout(input_layout)

    def log(self, text):
        self.chat_history.append(text)
        self.chat_history.moveCursor(QTextCursor.End)

    def send_command(self):
        user_text = self.input_field.text().strip()
        if not user_text: return
        self.input_field.clear()
        
        self.log(f"➔ Вы: {user_text}")
        
        # Запуск фонового рабочего потока
        self.worker = NetworkWorker(user_text)
        self.worker.result_signal.connect(self.log)
        self.worker.start()

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
    
