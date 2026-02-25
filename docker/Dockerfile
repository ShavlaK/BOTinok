# Dockerfile для VPN бота
FROM python:3.11-slim

# Метаданные
LABEL maintainer="YOUR_USERNAME"
LABEL version="1.0.0"
LABEL description="VPN Bot for Telegram"

# Рабочая директория
WORKDIR /app

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements
COPY bot/requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копируем файлы бота
COPY bot/ .

# Создаём директорию для данных
RUN mkdir -p /app/data /app/logs

# Точка входа
CMD ["python", "bot.py"]
