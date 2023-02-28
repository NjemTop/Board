# Задаем базовый образ для контейнера
FROM python:3.10

# Копируем файлы проекта в контейнер
COPY . /app

# Создаем директорию. logs внутри контейнера
RUN mkdir -p /app/logs

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r /app/requirements.txt

# Задаем рабочую директорию
WORKDIR /app

# Запускаем команду для запуска приложения
CMD ["python", "main.py"]
