# Используем официальный легковесный образ Python 3.11
FROM python:3.11-slim

# Задаём рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл зависимостей в контейнер
COPY requirements.txt .

# Устанавливаем зависимости из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в рабочую директорию контейнера
COPY . .

# Определяем команду запуска приложения
CMD ["python", "main.py"]
