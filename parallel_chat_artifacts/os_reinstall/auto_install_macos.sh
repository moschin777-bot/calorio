#!/bin/bash

# Автоматическая установка macOS 13/14 через OpenCore Legacy Patcher
# Выполняется полностью автоматически

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Автоматическая установка macOS 13/14${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Проверка модели
MODEL=$(system_profiler SPHardwareDataType | grep "Model Identifier" | awk '{print $3}')
CURRENT_VERSION=$(sw_vers -productVersion)

echo -e "${GREEN}✓ Модель: ${MODEL}${NC}"
echo -e "${GREEN}✓ Текущая версия: macOS ${CURRENT_VERSION}${NC}"
echo ""

# Выбор версии (по умолчанию macOS 13, так как более стабильная)
MACOS_VERSION="Ventura"
MACOS_VERSION_NUM="13"

echo -e "${BLUE}Выбираю macOS 13 Ventura (более стабильная)${NC}"
echo ""

# Создание директории для загрузок
DOWNLOAD_DIR="$HOME/Downloads/macos_installer"
mkdir -p "$DOWNLOAD_DIR"
cd "$DOWNLOAD_DIR"

echo -e "${BLUE}📥 Шаг 1: Загрузка OpenCore Legacy Patcher...${NC}"

# Получение URL последней версии OCLP
OCLP_URL=$(curl -s "https://api.github.com/repos/dortania/OpenCore-Legacy-Patcher/releases/latest" | \
    grep -o '"browser_download_url": "[^"]*GUI[^"]*\.dmg"' | \
    head -1 | \
    sed 's/.*"browser_download_url": "\([^"]*\)".*/\1/')

if [ -z "$OCLP_URL" ]; then
    # Альтернативный способ
    OCLP_URL=$(curl -s "https://api.github.com/repos/dortania/OpenCore-Legacy-Patcher/releases/latest" | \
        grep -o 'https://[^"]*\.dmg' | \
        grep -i GUI | \
        head -1)
fi

if [ -z "$OCLP_URL" ]; then
    echo -e "${RED}✗ Не удалось найти ссылку на OCLP${NC}"
    echo -e "${YELLOW}   Открываю страницу загрузки вручную...${NC}"
    open "https://github.com/dortania/OpenCore-Legacy-Patcher/releases/latest"
    exit 1
fi

echo -e "${GREEN}✓ Найдена ссылка: ${OCLP_URL}${NC}"
echo -e "${BLUE}   Загружаю OCLP...${NC}"

# Загрузка OCLP
curl -L -o "OpenCore-Patcher.dmg" "$OCLP_URL" || {
    echo -e "${RED}✗ Ошибка при загрузке OCLP${NC}"
    exit 1
}

echo -e "${GREEN}✓ OCLP загружен${NC}"
echo ""

# Монтирование DMG
echo -e "${BLUE}📦 Шаг 2: Установка OpenCore Legacy Patcher...${NC}"

hdiutil attach "OpenCore-Patcher.dmg" -quiet -nobrowse || {
    echo -e "${RED}✗ Ошибка при монтировании DMG${NC}"
    exit 1
}

# Поиск приложения в смонтированном образе
VOLUME_NAME=$(hdiutil info | grep -A 1 "OpenCore-Patcher.dmg" | tail -1 | awk '{$1=$2=$3=""; print $0}' | sed 's/^ *//')
APP_PATH="/Volumes/${VOLUME_NAME}/OpenCore Legacy Patcher.app"

if [ ! -d "$APP_PATH" ]; then
    # Попытка найти приложение по другому пути
    APP_PATH=$(find "/Volumes" -name "OpenCore Legacy Patcher.app" -type d 2>/dev/null | head -1)
fi

if [ -z "$APP_PATH" ] || [ ! -d "$APP_PATH" ]; then
    echo -e "${RED}✗ Приложение OCLP не найдено в DMG${NC}"
    hdiutil detach "/Volumes/${VOLUME_NAME}" 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✓ Найдено приложение: ${APP_PATH}${NC}"

# Копирование в Applications
echo -e "${BLUE}   Копирую в /Applications...${NC}"
cp -R "$APP_PATH" "/Applications/" || {
    echo -e "${YELLOW}⚠️  Не удалось скопировать автоматически${NC}"
    echo -e "${YELLOW}   Пожалуйста, скопируйте вручную:${NC}"
    echo -e "${YELLOW}   ${APP_PATH} -> /Applications/${NC}"
}

# Размонтирование
hdiutil detach "/Volumes/${VOLUME_NAME}" -quiet || true

echo -e "${GREEN}✓ OpenCore Legacy Patcher установлен${NC}"
echo ""

# Проверка установки
if [ ! -d "/Applications/OpenCore Legacy Patcher.app" ]; then
    echo -e "${YELLOW}⚠️  Приложение не найдено в /Applications${NC}"
    echo -e "${YELLOW}   Пожалуйста, установите вручную из: ${DOWNLOAD_DIR}/OpenCore-Patcher.dmg${NC}"
else
    echo -e "${GREEN}✓ Приложение готово к использованию${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Следующие шаги:${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "1. Откройте приложение:"
echo "   open '/Applications/OpenCore Legacy Patcher.app'"
echo ""
echo "2. В OCLP выберите:"
echo "   - 'Create macOS Installer'"
echo "   - Выберите macOS ${MACOS_VERSION_NUM} ${MACOS_VERSION}"
echo ""
echo "3. Следуйте инструкциям OCLP для завершения установки"
echo ""
echo -e "${GREEN}✓ Подготовка завершена!${NC}"
echo ""

# Автоматическое открытие приложения
read -p "Открыть OpenCore Legacy Patcher сейчас? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]] || [ -z "$REPLY" ]; then
    echo -e "${BLUE}🚀 Открываю OpenCore Legacy Patcher...${NC}"
    open "/Applications/OpenCore Legacy Patcher.app" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  Не удалось открыть автоматически${NC}"
        echo -e "${YELLOW}   Откройте вручную из /Applications${NC}"
    }
fi

