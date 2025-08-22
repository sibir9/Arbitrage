# Используем официальный Python образ (лучше брать slim-версию для легковесности)  
FROM python:3.11-slim  
  
# Создаем пользователя с ограниченными правами  
RUN useradd -m appuser  
  
# Рабочая директория приложения  
WORKDIR /app  
  
# Копируем файлы приложения в контейнер  
COPY . /app  

EXPOSE 5000
  
# Создаем и активируем виртуальное окружение, устанавливаем зависимости под non-root пользователем  
RUN python -m venv /app/venv && \  
    /bin/bash -c "source /app/venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"  
  
# Меняем пользователя на appuser  
USER appuser  
  
# Добавляем виртуальное окружение в PATH для удобства запуска  
ENV PATH="/app/venv/bin:$PATH"  
  
# Команда запуска вашего Flask-приложения через Gunicorn (пример)  
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
