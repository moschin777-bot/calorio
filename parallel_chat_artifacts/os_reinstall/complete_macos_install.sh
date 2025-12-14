#!/bin/bash

# Полностью автоматизированная установка macOS 13/14
# Автоматически находит и устанавливает OCLP, затем запускает процесс установки

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Полная автоматическая установка macOS${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

MODEL=$(system_profiler SPHardwareDataType | grep "Model Identifier" | awk '{print $3}')
CURRENT_VERSION=$(sw_vers -productVersion)

echo -e "${GREEN}✓ Модель: ${MODEL}${NC}"
echo -e "${GREEN}✓ Текущая версия: macOS ${CURRENT_VERSION}${NC}"
echo ""

# Создание рабочей директории
WORK_DIR="$HOME/macos_installer_auto"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# Поиск уже загруженного DMG файла
echo -e "${BLUE}🔍 Поиск OpenCore Legacy Patcher...${NC}"

DMG_FILE=""
SEARCH_PATHS=(
    "$WORK_DIR"
    "$HOME/Downloads"
    "$HOME/Desktop"
)

for SEARCH_PATH in "${SEARCH_PATHS[@]}"; do
    if [ -d "$SEARCH_PATH" ]; then
        FOUND=$(find "$SEARCH_PATH" -maxdepth 2 -name "*OpenCore*.dmg" -o -name "*OCLP*.dmg" 2>/dev/null | head -1)
        if [ ! -z "$FOUND" ] && [ -f "$FOUND" ]; then
            FILE_SIZE=$(stat -f%z "$FOUND" 2>/dev/null || stat -c%s "$FOUND" 2>/dev/null || echo 0)
            if [ "$FILE_SIZE" -gt 1000000 ]; then  # Больше 1MB
                DMG_FILE="$FOUND"
                echo -e "${GREEN}✓ Найден файл: $(basename "$DMG_FILE") ($(du -h "$DMG_FILE" | cut -f1))${NC}"
                break
            fi
        fi
    fi
done

# Если файл не найден, открываем страницу загрузки
if [ -z "$DMG_FILE" ]; then
    echo -e "${YELLOW}⚠️  Файл OCLP не найден${NC}"
    echo -e "${BLUE}   Открываю страницу загрузки...${NC}"
    open "https://github.com/dortania/OpenCore-Legacy-Patcher/releases/latest"
    echo ""
    echo -e "${YELLOW}Пожалуйста, скачайте файл .dmg с GitHub${NC}"
    echo -e "${YELLOW}После загрузки нажмите Enter...${NC}"
    read -p ""
    
    # Повторный поиск
    for SEARCH_PATH in "${SEARCH_PATHS[@]}"; do
        if [ -d "$SEARCH_PATH" ]; then
            FOUND=$(find "$SEARCH_PATH" -maxdepth 2 -name "*OpenCore*.dmg" -o -name "*OCLP*.dmg" 2>/dev/null | head -1)
            if [ ! -z "$FOUND" ] && [ -f "$FOUND" ]; then
                FILE_SIZE=$(stat -f%z "$FOUND" 2>/dev/null || stat -c%s "$FOUND" 2>/dev/null || echo 0)
                if [ "$FILE_SIZE" -gt 1000000 ]; then
                    DMG_FILE="$FOUND"
                    echo -e "${GREEN}✓ Найден файл: $(basename "$DMG_FILE")${NC}"
                    break
                fi
            fi
        fi
    done
fi

if [ -z "$DMG_FILE" ] || [ ! -f "$DMG_FILE" ]; then
    echo -e "${RED}✗ Файл не найден${NC}"
    exit 1
fi

# Монтирование и установка
echo ""
echo -e "${BLUE}📦 Установка OpenCore Legacy Patcher...${NC}"

# Монтирование DMG
MOUNT_OUTPUT=$(hdiutil attach "$DMG_FILE" -nobrowse -noverify -noautoopen 2>&1)
MOUNT_POINT=$(echo "$MOUNT_OUTPUT" | grep -o '/Volumes/[^[:space:]]*' | head -1)

if [ -z "$MOUNT_POINT" ]; then
    echo -e "${RED}✗ Не удалось смонтировать DMG${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Смонтировано: $MOUNT_POINT${NC}"

# Поиск приложения
APP_PATH=$(find "$MOUNT_POINT" -name "*.app" -type d -maxdepth 3 | head -1)

if [ -z "$APP_PATH" ]; then
    echo -e "${RED}✗ Приложение не найдено в DMG${NC}"
    hdiutil detach "$MOUNT_POINT" 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✓ Найдено приложение: $(basename "$APP_PATH")${NC}"

# Копирование в Applications
echo -e "${BLUE}   Копирую в /Applications...${NC}"
rm -rf "/Applications/OpenCore Legacy Patcher.app" 2>/dev/null || true

if cp -R "$APP_PATH" "/Applications/" 2>/dev/null; then
    echo -e "${GREEN}✓ Успешно скопировано${NC}"
else
    echo -e "${YELLOW}⚠️  Требуется разрешение. Копирую вручную...${NC}"
    # Попытка через ditto
    ditto "$APP_PATH" "/Applications/$(basename "$APP_PATH")" 2>/dev/null || {
        echo -e "${YELLOW}   Пожалуйста, скопируйте вручную:${NC}"
        echo -e "${YELLOW}   ${APP_PATH} -> /Applications/${NC}"
        open "$MOUNT_POINT"
    }
fi

# Размонтирование
hdiutil detach "$MOUNT_POINT" -quiet 2>/dev/null || true

# Проверка и запуск
if [ -d "/Applications/OpenCore Legacy Patcher.app" ]; then
    echo ""
    echo -e "${GREEN}✓ OpenCore Legacy Patcher установлен!${NC}"
    echo ""
    echo -e "${BLUE}🚀 Запускаю приложение...${NC}"
    sleep 1
    open "/Applications/OpenCore Legacy Patcher.app"
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Установка завершена!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}В OpenCore Legacy Patcher:${NC}"
    echo "  1. Нажмите 'Create macOS Installer'"
    echo "  2. Выберите macOS 13 Ventura (рекомендуется) или macOS 14 Sonoma"
    echo "  3. Следуйте инструкциям OCLP"
    echo ""
    echo -e "${YELLOW}⚠️  ВАЖНО:${NC}"
    echo "  • Убедитесь, что создана резервная копия"
    echo "  • Процесс установки займет 30-60 минут"
    echo "  • Не выключайте Mac во время установки"
    echo ""
else
    echo -e "${YELLOW}⚠️  Приложение не найдено в /Applications${NC}"
    echo -e "${YELLOW}   Пожалуйста, установите вручную${NC}"
fi

echo -e "${GREEN}✓ Готово!${NC}"

