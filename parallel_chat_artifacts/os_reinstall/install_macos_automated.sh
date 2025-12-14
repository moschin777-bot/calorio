#!/bin/bash

# Полностью автоматизированная установка macOS 13/14
# Выполняет все шаги автоматически

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

MODEL=$(system_profiler SPHardwareDataType | grep "Model Identifier" | awk '{print $3}')
echo -e "${GREEN}✓ Модель: ${MODEL}${NC}"

# Создание рабочей директории
WORK_DIR="$HOME/macos_installer_auto"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

echo -e "${BLUE}📥 Шаг 1: Получение информации о последней версии OCLP...${NC}"

# Получение информации о релизах
RELEASE_INFO=$(curl -s "https://api.github.com/repos/dortania/OpenCore-Legacy-Patcher/releases/latest")
TAG_NAME=$(echo "$RELEASE_INFO" | python3 -c "import sys, json; print(json.load(sys.stdin).get('tag_name', ''))" 2>/dev/null || echo "")

if [ -z "$TAG_NAME" ]; then
    TAG_NAME="2.4.1"  # Последняя известная версия
fi

echo -e "${GREEN}✓ Версия OCLP: ${TAG_NAME}${NC}"

# Попытка найти правильный URL для загрузки
echo -e "${BLUE}📦 Шаг 2: Поиск установочного файла...${NC}"

# Варианты имен файлов
POSSIBLE_NAMES=(
    "OpenCore-Patcher-GUI.app.dmg"
    "OpenCore-Patcher.app.dmg"
    "OpenCore-Legacy-Patcher-GUI.dmg"
    "OpenCore-Legacy-Patcher.dmg"
)

OCLP_URL=""
for NAME in "${POSSIBLE_NAMES[@]}"; do
    TEST_URL="https://github.com/dortania/OpenCore-Legacy-Patcher/releases/download/${TAG_NAME}/${NAME}"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$TEST_URL" --max-time 5)
    if [ "$HTTP_CODE" = "200" ]; then
        OCLP_URL="$TEST_URL"
        echo -e "${GREEN}✓ Найден файл: ${NAME}${NC}"
        break
    fi
done

if [ -z "$OCLP_URL" ]; then
    echo -e "${YELLOW}⚠️  Не удалось найти прямую ссылку${NC}"
    echo -e "${BLUE}   Открываю страницу загрузки в браузере...${NC}"
    open "https://github.com/dortania/OpenCore-Legacy-Patcher/releases/latest"
    echo ""
    echo -e "${YELLOW}Пожалуйста, скачайте файл вручную:${NC}"
    echo "  1. Найдите файл с расширением .dmg"
    echo "  2. Сохраните его в: $WORK_DIR"
    echo "  3. Запустите скрипт снова"
    echo ""
    read -p "Нажмите Enter после загрузки файла..."
    
    # Поиск загруженного файла
    DMG_FILE=$(find "$WORK_DIR" -name "*.dmg" -type f | head -1)
    if [ -z "$DMG_FILE" ]; then
        DMG_FILE=$(find "$HOME/Downloads" -name "*OpenCore*.dmg" -type f | head -1)
    fi
else
    echo -e "${BLUE}📥 Шаг 3: Загрузка OpenCore Legacy Patcher...${NC}"
    curl -L --progress-bar -o "OpenCore-Patcher.dmg" "$OCLP_URL" || {
        echo -e "${RED}✗ Ошибка при загрузке${NC}"
        exit 1
    }
    DMG_FILE="$WORK_DIR/OpenCore-Patcher.dmg"
fi

if [ ! -f "$DMG_FILE" ] || [ ! -s "$DMG_FILE" ]; then
    echo -e "${RED}✗ Файл не найден или пуст${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Файл готов: $(basename "$DMG_FILE") ($(du -h "$DMG_FILE" | cut -f1))${NC}"
echo ""

# Монтирование DMG
echo -e "${BLUE}📦 Шаг 4: Установка OpenCore Legacy Patcher...${NC}"

MOUNT_POINT=$(hdiutil attach "$DMG_FILE" -nobrowse -noverify -noautoopen 2>&1 | grep -E '^/dev/' | sed 's/.*\(Volumes\/.*\)/\1/' | head -1)

if [ -z "$MOUNT_POINT" ]; then
    MOUNT_POINT=$(hdiutil attach "$DMG_FILE" -nobrowse 2>&1 | tail -1 | awk '{$1=$2=$3=""; print $0}' | sed 's/^ *//' | sed 's/.*\(Volumes\/.*\)/\1/')
fi

if [ -z "$MOUNT_POINT" ]; then
    echo -e "${RED}✗ Не удалось смонтировать DMG${NC}"
    exit 1
fi

VOLUME_PATH="/Volumes/${MOUNT_POINT#Volumes/}"
APP_PATH=$(find "$VOLUME_PATH" -name "*.app" -type d | head -1)

if [ -z "$APP_PATH" ]; then
    echo -e "${RED}✗ Приложение не найдено в DMG${NC}"
    hdiutil detach "$VOLUME_PATH" 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✓ Найдено приложение: $(basename "$APP_PATH")${NC}"

# Копирование в Applications
echo -e "${BLUE}   Копирую в /Applications...${NC}"
rm -rf "/Applications/OpenCore Legacy Patcher.app" 2>/dev/null || true
cp -R "$APP_PATH" "/Applications/" || {
    echo -e "${YELLOW}⚠️  Требуется разрешение для копирования${NC}"
    echo -e "${YELLOW}   Пожалуйста, разрешите доступ в настройках безопасности${NC}"
}

# Размонтирование
hdiutil detach "$VOLUME_PATH" -quiet 2>/dev/null || true

# Проверка установки
if [ -d "/Applications/OpenCore Legacy Patcher.app" ]; then
    echo -e "${GREEN}✓ OpenCore Legacy Patcher успешно установлен!${NC}"
    echo ""
    
    # Открытие приложения
    echo -e "${BLUE}🚀 Открываю OpenCore Legacy Patcher...${NC}"
    sleep 2
    open "/Applications/OpenCore Legacy Patcher.app" || {
        echo -e "${YELLOW}⚠️  Не удалось открыть автоматически${NC}"
        echo -e "${YELLOW}   Откройте вручную из /Applications${NC}"
    }
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Установка завершена!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}Следующие шаги в OpenCore Legacy Patcher:${NC}"
    echo "  1. Выберите 'Create macOS Installer'"
    echo "  2. Выберите macOS 13 Ventura (рекомендуется) или macOS 14 Sonoma"
    echo "  3. Следуйте инструкциям OCLP"
    echo ""
else
    echo -e "${YELLOW}⚠️  Приложение не найдено в /Applications${NC}"
    echo -e "${YELLOW}   Пожалуйста, установите вручную из: ${APP_PATH}${NC}"
fi

# Очистка
cd "$HOME"
echo -e "${BLUE}🧹 Очистка временных файлов...${NC}"
# Не удаляем DMG, может пригодиться

echo ""
echo -e "${GREEN}✓ Готово!${NC}"

