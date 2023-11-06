FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y locales wget && \
    echo "ru_RU.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen ru_RU.UTF-8 && \
    update-locale LANG=ru_RU.UTF-8 && \
    wget -q https://packages.microsoft.com/config/debian/10/packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    apt-get update && \
    apt-get install -y powershell && \
    apt-get clean && \
    apt-get update --fix-missing

RUN mkdir -p ./backup && \
    mkdir -p /app/logs && \
    mkdir -p /app/backup

RUN apt-get update && \
    apt-get install -y smbclient cifs-utils

RUN mkdir /mnt/windows_share

ENV LANG=ru_RU.UTF-8 LANGUAGE=ru_RU:en LC_ALL=ru_RU.UTF-8

COPY . /app

RUN pip install --no-cache-dir -r /app/requirements.txt

WORKDIR /app

CMD ["python", "main.py"]
