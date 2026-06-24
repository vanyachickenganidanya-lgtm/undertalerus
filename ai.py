import os
import json
import subprocess
import requests
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QLineEdit, QPushButton)
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtCore import Qt, QThread, Signal

# --- КОНФИГУРАЦИЯ ---
API_KEY = "ТВОЙ_OPENROUTER_API_KEY"  # Вставь свой ключ сюда, бро!
URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "google/gemini-3.5-flash"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost",
    "X-Title": "Gemini+ Ultimate OS Agent"
}

# --- ИНСТРУМЕНТЫ РАБОТЫ С ОС ---
def get_file(path):
    """get.file(место) - Чтение файла"""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f"Ошибка чтения: {str(e)}"

def create_file(path, filename):
    """create.file(место, название) - Создание файла"""
    try:
        full_path = os.path.join(path, filename)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write("")
        return f"Успех: Создан {full_path}"
    except Exception as e:
        return f"Ошибка создания: {str(e)}"

def write_file(path, content):
    """write.file(место, текст) - Запись в файл"""
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(content + "\n")
        return f"Успех: Записано в {path}"
    except Exception as e:
        return f"Ошибка записи: {str(e)}"

def get_files(folder_path):
    """get.files(папка) - Список файлов"""
    try:
        if os.path.exists(folder_path):
            return "\n".join(os.listdir(folder_path))
        return "Ошибка: Папка не существует."
    except Exception as e:
        return f"Ошибка: {str(e)}"

def run_cmd(command):
    """Выполнение терминальных команд (CMD/Bash)"""
    try:
        res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30, encoding="cp866")
        return res.stdout if res.stdout else res.stderr
    except Exception as e:
        return f"Ошибка терминала: {str(e)}"

def run_python(code):
    """Выполнение Python-кода"""
    try:
        res = subprocess.run(["python", "-c", code], capture_output=True, text=True, timeout=15)
        return res.stdout if res.stdout else res.stderr
    except Exception as e:
        return f"Ошибка Python: {str(e)}"

def run_cpp(code, exe_name="temp_ai_app"):
    """Компиляция C++ через g++ и мгновенный запуск"""
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
        
        return run_res.stdout if run_res.stdout else run_res.stderr
    except Exception as e:
        return f"Ошибка среды C++: {str(e)}"

# Карта функций для автовызова
tools_map = {
    "get_file": get_file, "create_file": create_file, "write_file": write_file,
    "get_files": get_files, "run_cmd": run_cmd, "run_python": run_python, "run_cpp": run_cpp
}

# Описание схем для Gemini+
tools_definition = [
    {"type": "function", "function": {"name": "get_file", "description": "Аналог get.file(место). Читает файл.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "create_file", "description": "Аналог create.file(место, название). Создает файл.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "filename": {"type": "string"}}, "required": ["path", "filename"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Аналог write.file(место, текст). Пишет текст.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "get_files", "description": "Аналог get.files(папка). Список файлов.", "parameters": {"type": "object", "properties": {"folder_path": {"type": "string"}}, "required": ["folder_path"]}}},
    {"type": "function", "function": {"name": "run_cmd", "description": "Выполнить cmd/bash команду.", "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "run_python", "description": "Запустить Python-код.", "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}},
    {"type": "function", "function": {"name": "run_cpp", "description": "Компиляция и запуск C++.", "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}}
]

# Простой парсер Markdown в HTML
def parse_markdown(text):
    import re
    html = text.replace('\n', '<br>')
    html = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', html)
    html = re.sub(r'\*(.*?)\*', r'<i>\1</i>', html)
    html = re.sub(r'
