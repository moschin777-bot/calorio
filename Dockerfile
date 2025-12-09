# Multi-stage build для уменьшения размера образа

# Stage 1: Builder
FROM python:3.11-slim as builder

# Установка системных зависимостей для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Создание виртуального окружения
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копирование requirements.txt и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Установка только runtime зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя для запуска приложения (не root)
RUN useradd -m -u 1000 calorio && \
    mkdir -p /app /app/logs /app/media /app/staticfiles && \
    chown -R calorio:calorio /app

# Копирование виртуального окружения из builder stage
COPY --from=builder /opt/venv /opt/venv

# Установка рабочей директории
WORKDIR /app

# Копирование кода приложения
COPY --chown=calorio:calorio . .

# Установка переменных окружения
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Переключение на непривилегированного пользователя
USER calorio

# Expose порт
EXPOSE 8000

# Копирование и установка прав на entrypoint скрипт
COPY --chown=calorio:calorio entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Команда по умолчанию
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "calorio_api.wsgi:application"]

