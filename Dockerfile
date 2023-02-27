# Задаем базовый образ для контейнера
FROM python:3.9-slim-buster

# Копируем файлы проекта в контейнер
COPY . /app

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r /app/requirements.txt

# Задаем рабочую директорию
WORKDIR /app

# Запускаем команду для запуска приложения
CMD ["python", "main.py"]
