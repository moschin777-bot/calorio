#!/bin/bash
# Скрипт для запуска всех тестов

# Активируем виртуальное окружение
source venv/bin/activate

# Запускаем pytest
pytest -v --tb=short --reuse-db

