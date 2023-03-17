FROM python:3.10

# Устанавливаем PowerShell
RUN wget -q https://packages.microsoft.com/config/debian/10/packages-microsoft-prod.deb
RUN dpkg -i packages-microsoft-prod.deb
RUN apt-get update && apt-get install -y powershell

# Копируем файлы проекта в контейнер
COPY . /app

# Создаем директорию logs внутри контейнера
RUN mkdir -p /app/logs

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r /app/requirements.txt

# Очищаем кэш и обновляем список пакетов
RUN apt-get clean && \
    apt-get update --fix-missing

# Задаем рабочую директорию
WORKDIR /app

# Запускаем команду для запуска приложения
CMD ["python", "main.py"]
