import os
import json
import subprocess
import requests  # Вместо openai используем прямые запросы
import customtkinter as ctk

# 1. НАСТРОЙКА КЛИЕНТА (Прямые запросы к OpenRouter)
API_KEY = "ТВОЙ_OPENROUTER_API_KEY"  # <-- Сюда свой ключ
URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "google/gemini-3.5-flash"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost",
    "X-Title": "Gemini+ OS Agent"
}

# 2. РЕАЛИЗАЦИЯ ТВОИХ КОМАНД И ИНСТРУМЕНТОВ
def get_file(path):
    """get.file(место) - Читает файл"""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f"--- Содержимое {path} ---\n{f.read()}"
    except Exception as e:
        return f"Ошибка чтения файла: {str(e)}"

def create_file(path, filename):
    """create.file(место, название) - Создает пустой файл"""
    try:
        full_path = os.path.join(path, filename)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write("")
        return f"Успех: Файл создан по пути {full_path}"
    except Exception as e:
        return f"Ошибка создания файла: {str(e)}"

def write_file(path, content):
    """write.file(место, что написать) - Записывает/дописывает текст в файл"""
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(content + "\n")
        return f"Успех: Данные записаны в {path}"
    except Exception as e:
        return f"Ошибка записи: {str(e)}"

def get_files(folder_path):
    """get.files(место папки) - Показывает список файлов в директории"""
    try:
        if os.path.exists(folder_path):
            files = os.listdir(folder_path)
            return f"Файлы в {folder_path}:\n" + "\n".join(files)
        return "Ошибка: Указанная папка не существует."
    except Exception as e:
        return f"Ошибка получения списка: {str(e)}"

def run_cmd(command):
    """Доступ к консоли (CMD/Bash/Pacman)"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30, encoding="cp866")
        output = result.stdout if result.stdout else result.stderr
        return f"Команда выполнена. Вывод:\n{output}"
    except Exception as e:
        return f"Ошибка выполнения терминала: {str(e)}"

def run_python(code):
    """Доступ к исполнению Python на лету"""
    try:
        result = subprocess.run(["python", "-c", code], capture_output=True, text=True, timeout=15)
        output = result.stdout if result.stdout else result.stderr
        return f"Вывод Python:\n{output}"
    except Exception as e:
        return f"Ошибка интерпретатора Python: {str(e)}"

def run_cpp(code, exe_name="temp_ai_app"):
    """Компиляция C++ (g++) и запуск"""
    try:
        cpp_file = f"{exe_name}.cpp"
        with open(cpp_file, "w", encoding="utf-8") as f:
            f.write(code)
        
        compile_res = subprocess.run(["g++", cpp_file, "-o", exe_name], capture_output=True, text=True)
        if compile_res.returncode != 0:
            return f"❌ Ошибка компиляции g++:\n{compile_res.stderr}"
        
        run_res = subprocess.run([f"./{exe_name}" if os.name != 'nt' else f"{exe_name}.exe"], capture_output=True, text=True)
        
        if os.path.exists(cpp_file): os.remove(cpp_file)
        if os.path.exists(f"{exe_name}.exe"): os.remove(f"{exe_name}.exe")
        
        return f"🚀 Успешный запуск C++!\nВывод программы:\n{run_res.stdout}"
    except Exception as e:
        return f"Ошибка среды C++: {str(e)}"

# Маппинг для вызова функций
tools_map = {
    "get_file": get_file,
    "create_file": create_file,
    "write_file": write_file,
    "get_files": get_files,
    "run_cmd": run_cmd,
    "run_python": run_python,
    "run_cpp": run_cpp
}

# Описание инструментов для Gemini 3.5 Flash (формат JSON-схемы остался прежним)
tools_definition = [
    {"type": "function", "function": {"name": "get_file", "description": "Аналог get.file(место). Читает файл.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "create_file", "description": "Аналог create.file(место, название). Создает пустой файл.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "filename": {"type": "string"}}, "required": ["path", "filename"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Аналог write.file(место, что написать). Пишет текст в файл.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "get_files", "description": "Аналог get.files(место папки). Показывает список файлов.", "parameters": {"type": "object", "properties": {"folder_path": {"type": "string"}}, "required": ["folder_path"]}}},
    {"type": "function", "function": {"name": "run_cmd", "description": "Запускает любые команды в консоли (cmd/bash/pacman).", "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "run_python", "description": "Выполняет чистый скрипт на Python и возвращает вывод.", "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}},
    {"type": "function", "function": {"name": "run_cpp", "description": "Принимает исходный код C++, компилирует его через g++ и запускает.", "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}}
]

# 3. ИНТЕРФЕЙС ПРИЛОЖЕНИЯ
class SuperAIAgentGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gemini+ Ultimate OS Agent (Pure HTTP)")
        self.geometry("700x550")
        ctk.set_appearance_mode("dark")

        self.chat_history = ctk.CTkTextbox(self, width=660, height=400, font=("Consolas", 12))
        self.chat_history.pack(pady=20, padx=20)
        self.chat_history.insert("0.0", "Система: Агент готов. Работает напрямую через API OpenRouter.\n\n")
        self.chat_history.configure(state="disabled")

        self.input_field = ctk.CTkEntry(self, width=500, placeholder_text="Прикажи мне что-нибудь...")
        self.input_field.pack(side="left", padx=(20, 10), pady=(0, 20))
        self.input_field.bind("<Return>", lambda event: self.send_command())

        self.send_btn = ctk.CTkButton(self, text="Выполнить", width=140, command=self.send_command)
        self.send_btn.pack(side="right", padx=(0, 20), pady=(0, 20))

    def log(self, text):
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", text + "\n")
        self.chat_history.configure(state="disabled")
        self.chat_history.see("end")

    def send_command(self):
        user_text = self.input_field.get().strip()
        if not user_text: return
        self.input_field.delete(0, "end")
        self.log(f"➔ Вы: {user_text}")

        # Сборка структуры JSON-запроса вручную
        payload = {
            "model": MODEL_NAME,
            "messages": [{
                "role": "user", 
                "content": f"Ты системный помощник. Выполни задачу пользователя, используя подходящий инструмент: {user_text}"
            }],
            "tools": tools_definition,
            "tool_choice": "auto"
        }

        try:
            # Прямой POST-запрос на сервера OpenRouter
            response = requests.post(URL, headers=headers, data=json.dumps(payload), timeout=60)
            
            if response.status_code != 200:
                self.log(f"❌ Ошибка сервера OpenRouter ({response.status_code}): {response.text}\n")
                return

            response_json = response.json()
            message = response_json['choices'][0]['message']

            # Проверяем, вернула ли модель вызовы функций (tool_calls)
            if 'tool_calls' in message and message['tool_calls']:
                for call in message['tool_calls']:
                    f_name = call['function']['name']
                    # Извлекаем аргументы из строки в словарь Python
                    args = json.loads(call['function']['arguments'])
                    
                    self.log(f"🤖 [Вызов {f_name}] с аргументами: {args}")
                    
                    if f_name in tools_map:
                        res = tools_map[f_name](**args)
                        self.log(f"{res}\n")
            else:
                # Обычный текстовый ответ модели
                self.log(f"🤖 ИИ: {message.get('content', '')}\n")
                
        except Exception as e:
            self.log(f"❌ Ошибка выполнения: {str(e)}\n")

if __name__ == "__main__":
    app = SuperAIAgentGUI()
    app.mainloop()
tools_definition = [
    {"type": "function", "function": {"name": "get_file", "description": "Аналог get.file(место). Читает файл.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "create_file", "description": "Аналог create.file(место, название). Создает пустой файл.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "filename": {"type": "string"}}, "required": ["path", "filename"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Аналог write.file(место, что написать). Пишет текст в файл.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "get_files", "description": "Аналог get.files(место папки). Показывает список файлов.", "parameters": {"type": "object", "properties": {"folder_path": {"type": "string"}}, "required": ["folder_path"]}}},
    {"type": "function", "function": {"name": "run_cmd", "description": "Запускает любые команды в консоли (cmd/bash/pacman).", "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "run_python", "description": "Выполняет чистый скрипт на Python и возвращает вывод.", "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}},
    {"type": "function", "function": {"name": "run_cpp", "description": "Принимает исходный код C++, компилирует его через g++ и запускает.", "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}}
]

# 3. ИНТЕРФЕЙС ПРИЛОЖЕНИЯ
class SuperAIAgentGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gemini+ Ultimate OS Agent")
        self.geometry("700x550")
        ctk.set_appearance_mode("dark")

        self.chat_history = ctk.CTkTextbox(self, width=660, height=400, font=("Consolas", 12))
        self.chat_history.pack(pady=20, padx=20)
        self.chat_history.insert("0.0", "Система: Агент готов. Доступны: Файлы, CMD/Pacman, Python, C++ (g++)\n\n")
        self.chat_history.configure(state="disabled")

        self.input_field = ctk.CTkEntry(self, width=500, placeholder_text="Прикажи мне: откомпилируй код C++ с 'Hello World' или обнови систему...")
        self.input_field.pack(side="left", padx=(20, 10), pady=(0, 20))
        self.input_field.bind("<Return>", lambda event: self.send_command())

        self.send_btn = ctk.CTkButton(self, text="Выполнить", width=140, command=self.send_command)
        self.send_btn.pack(side="right", padx=(0, 20), pady=(0, 20))

    def log(self, text):
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", text + "\n")
        self.chat_history.configure(state="disabled")
        self.chat_history.see("end")

    def send_command(self):
        user_text = self.input_field.get().strip()
        if not user_text: return
        self.input_field.delete(0, "end")
        self.log(f"➔ Вы: {user_text}")

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{
                    "role": "user", 
                    "content": f"Ты системный помощник. Выполни задачу пользователя, используя подходящий инструмент: {user_text}"
                }],
                tools=tools_definition,
                tool_choice="auto",
                extra_headers=extra_headers
            )
            
            msg = response.choices[0].message
            if msg.tool_calls:
                for call in msg.tool_calls:
                    f_name = call.function.name
                    args = json.loads(call.function.arguments)
                    self.log(f"🤖 [Вызов {f_name}] с аргументами: {args}")
                    
                    if f_name in tools_map:
                        res = tools_map[f_name](**args)
                        self.log(f"{res}\n")
            else:
                self.log(f"🤖 ИИ: {msg.content}\n")
        except Exception as e:
            self.log(f"❌ Ошибка: {str(e)}\n")

if __name__ == "__main__":
    app = SuperAIAgentGUI()
    app.mainloop()
      
