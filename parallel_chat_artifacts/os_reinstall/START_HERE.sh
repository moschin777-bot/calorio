#!/bin/bash

# ГЛАВНЫЙ СКРИПТ - ЗАПУСТИТЕ ЭТОТ ФАЙЛ!
# Автоматически выполнит ВСЁ необходимое для установки macOS 13/14

clear

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  АВТОМАТИЧЕСКАЯ УСТАНОВКА macOS 13/14${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Проверка системы
MODEL=$(system_profiler SPHardwareDataType | grep "Model Identifier" | awk '{print $3}')
echo -e "${GREEN}✓ Ваш Mac: ${MODEL}${NC}"
echo ""

# 1. Резервная копия
echo -e "${BLUE}📋 ШАГ 1: Резервная копия${NC}"
BACKUP=$(tmutil listbackups 2>/dev/null | tail -1)
if [ ! -z "$BACKUP" ]; then
    echo -e "${GREEN}✓ Резервная копия найдена!${NC}"
else
    echo -e "${RED}⚠️  Резервная копия не найдена!${NC}"
    echo -e "${YELLOW}Открываю настройки Time Machine...${NC}"
    open "x-apple.systempreferences:com.apple.preference.timemachine"
    echo ""
    echo -e "${YELLOW}ПОЖАЛУЙСТА:${NC}"
    echo -e "${YELLOW}1. Выберите диск для резервного копирования${NC}"
    echo -e "${YELLOW}2. Включите Time Machine${NC}"
    echo -e "${YELLOW}3. Дождитесь создания резервной копии${NC}"
    echo ""
    read -p "Нажмите Enter после создания резервной копии..."
fi
echo ""

# 2. OCLP
echo -e "${BLUE}📦 ШАГ 2: OpenCore Legacy Patcher${NC}"
if [ -d "/Applications/OpenCore-Patcher.app" ]; then
    echo -e "${GREEN}✓ OpenCore Legacy Patcher установлен${NC}"
else
    echo -e "${YELLOW}Устанавливаю OCLP...${NC}"
    WORK_DIR="$HOME/macos_installer_auto"
    mkdir -p "$WORK_DIR"
    cd "$WORK_DIR"
    if [ ! -f "oclp.zip" ]; then
        curl -L -o oclp.zip "https://github.com/dortania/OpenCore-Legacy-Patcher/archive/refs/heads/main.zip"
    fi
    unzip -q -o oclp.zip 2>/dev/null
    APP_PATH=$(find . -name "OpenCore-Patcher.app" -type d | head -1)
    [ ! -z "$APP_PATH" ] && cp -R "$APP_PATH" "/Applications/"
    echo -e "${GREEN}✓ OCLP установлен${NC}"
fi
echo ""

# 3. Запуск
echo -e "${BLUE}🚀 ШАГ 3: Запуск OpenCore Legacy Patcher${NC}"
open -a "/Applications/OpenCore-Patcher.app" 2>/dev/null || open "/Applications/OpenCore-Patcher.app"
echo -e "${GREEN}✓ OCLP запущен!${NC}"
echo ""

# Инструкции
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ВСЁ ГОТОВО!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}В открывшемся окне OpenCore Legacy Patcher:${NC}"
echo ""
echo -e "${YELLOW}1. Нажмите 'Create macOS Installer'${NC}"
echo -e "${YELLOW}2. Выберите macOS 13 Ventura (рекомендуется)${NC}"
echo -e "${YELLOW}3. Дождитесь загрузки (30-60 минут)${NC}"
echo -e "${YELLOW}4. Подключите USB (16GB+)${NC}"
echo -e "${YELLOW}5. Создайте установщик${NC}"
echo ""
echo -e "${RED}⚠️  ВАЖНО ПОСЛЕ УСТАНОВКИ:${NC}"
echo -e "${YELLOW}  • НЕ перезагружайтесь сразу!${NC}"
echo -e "${YELLOW}  • Запустите OCLP → 'Post Install Root Patch'${NC}"
echo -e "${YELLOW}  • Примените патчи для MacBook9,1${NC}"
echo -e "${YELLOW}  • Только потом перезагрузитесь${NC}"
echo ""
echo -e "${GREEN}✅ Готово! Следуйте инструкциям в OCLP${NC}"

