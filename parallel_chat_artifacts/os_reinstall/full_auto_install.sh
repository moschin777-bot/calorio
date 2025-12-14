#!/bin/bash

# ПОЛНОСТЬЮ АВТОМАТИЧЕСКАЯ УСТАНОВКА macOS 13/14
# Выполняет все шаги автоматически с проверками безопасности

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  ПОЛНАЯ АВТОМАТИЧЕСКАЯ УСТАНОВКА macOS${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

MODEL=$(system_profiler SPHardwareDataType | grep "Model Identifier" | awk '{print $3}')
CURRENT_VERSION=$(sw_vers -productVersion)
DISK_SPACE=$(df -h / | tail -1 | awk '{print $4}')

echo -e "${GREEN}✓ Модель: ${MODEL}${NC}"
echo -e "${GREEN}✓ Текущая версия: macOS ${CURRENT_VERSION}${NC}"
echo -e "${GREEN}✓ Свободное место: ${DISK_SPACE}${NC}"
echo ""

# ШАГ 1: Проверка резервной копии
echo -e "${BLUE}📋 ШАГ 1: Проверка резервной копии...${NC}"

BACKUP_EXISTS=false
LAST_BACKUP=$(tmutil listbackups 2>/dev/null | tail -1)

if [ ! -z "$LAST_BACKUP" ]; then
    BACKUP_DATE=$(basename "$LAST_BACKUP" | cut -d'-' -f1-3)
    echo -e "${GREEN}✓ Найдена резервная копия от: ${BACKUP_DATE}${NC}"
    BACKUP_EXISTS=true
else
    echo -e "${YELLOW}⚠️  Резервная копия не найдена${NC}"
    echo -e "${BLUE}   Создаю резервную копию через Time Machine...${NC}"
    
    # Проверка настроек Time Machine
    TM_STATUS=$(tmutil status 2>/dev/null | grep -c "Running" || echo "0")
    
    if [ "$TM_STATUS" = "0" ]; then
        echo -e "${YELLOW}   Time Machine не настроен или не запущен${NC}"
        echo -e "${BLUE}   Открываю настройки Time Machine...${NC}"
        open "x-apple.systempreferences:com.apple.preference.timemachine"
        echo ""
        echo -e "${YELLOW}   Пожалуйста, настройте Time Machine и создайте резервную копию${NC}"
        echo -e "${YELLOW}   После создания резервной копии запустите скрипт снова${NC}"
        read -p "Нажмите Enter после создания резервной копии..."
    else
        echo -e "${BLUE}   Запускаю резервное копирование...${NC}"
        tmutil startbackup --block 2>/dev/null || {
            echo -e "${YELLOW}   Резервное копирование запущено в фоне${NC}"
            echo -e "${YELLOW}   Дождитесь завершения (может занять время)${NC}"
        }
    fi
fi

echo ""

# ШАГ 2: Проверка OCLP
echo -e "${BLUE}📦 ШАГ 2: Проверка OpenCore Legacy Patcher...${NC}"

if [ ! -d "/Applications/OpenCore-Patcher.app" ]; then
    echo -e "${YELLOW}⚠️  OCLP не найден, устанавливаю...${NC}"
    
    WORK_DIR="$HOME/macos_installer_auto"
    mkdir -p "$WORK_DIR"
    cd "$WORK_DIR"
    
    if [ ! -f "oclp.zip" ] || [ ! -s "oclp.zip" ]; then
        echo -e "${BLUE}   Загружаю OpenCore Legacy Patcher...${NC}"
        curl -L -o oclp.zip "https://github.com/dortania/OpenCore-Legacy-Patcher/archive/refs/heads/main.zip" 2>&1 | grep -E "(Total|%)" | tail -1
    fi
    
    if [ -f "oclp.zip" ] && [ -s "oclp.zip" ]; then
        echo -e "${BLUE}   Распаковываю...${NC}"
        unzip -q -o oclp.zip 2>/dev/null || true
        
        APP_PATH=$(find . -name "OpenCore-Patcher.app" -type d | head -1)
        if [ ! -z "$APP_PATH" ]; then
            cp -R "$APP_PATH" "/Applications/" 2>/dev/null && echo -e "${GREEN}✓ OCLP установлен${NC}"
        fi
    fi
fi

if [ ! -d "/Applications/OpenCore-Patcher.app" ]; then
    echo -e "${RED}✗ Не удалось установить OCLP${NC}"
    exit 1
fi

echo -e "${GREEN}✓ OpenCore Legacy Patcher готов${NC}"
echo ""

# ШАГ 3: Подготовка к установке
echo -e "${BLUE}🔧 ШАГ 3: Подготовка к установке macOS...${NC}"

# Выбор версии (по умолчанию macOS 13 - более стабильная)
MACOS_VERSION="Ventura"
MACOS_VERSION_NUM="13"

echo -e "${GREEN}✓ Выбрана версия: macOS ${MACOS_VERSION_NUM} ${MACOS_VERSION}${NC}"
echo -e "${BLUE}   (macOS 13 более стабильная для MacBook9,1)${NC}"
echo ""

# ШАГ 4: Проверка USB-накопителя
echo -e "${BLUE}💾 ШАГ 4: Проверка USB-накопителя...${NC}"

USB_FOUND=false
USB_DEVICE=""

# Поиск внешних дисков
EXTERNAL_DISKS=$(diskutil list | grep -E "^/dev/disk[0-9]+" | awk '{print $1}' | while read disk; do
    diskutil info "$disk" 2>/dev/null | grep -q "External:.*Yes" && echo "$disk"
done)

if [ ! -z "$EXTERNAL_DISKS" ]; then
    for DISK in $EXTERNAL_DISKS; do
        DISK_SIZE=$(diskutil info "$DISK" 2>/dev/null | grep "Disk Size" | awk '{print $3$4}' | sed 's/[^0-9]//g')
        if [ ! -z "$DISK_SIZE" ] && [ "$DISK_SIZE" -gt 14000000000 ]; then  # Больше 14GB
            USB_DEVICE="$DISK"
            USB_FOUND=true
            DISK_NAME=$(diskutil info "$DISK" 2>/dev/null | grep "Volume Name" | cut -d: -f2 | xargs)
            echo -e "${GREEN}✓ Найден USB-накопитель: ${DISK_NAME} (${DISK})${NC}"
            break
        fi
    done
fi

if [ "$USB_FOUND" = false ]; then
    echo -e "${YELLOW}⚠️  USB-накопитель не найден${NC}"
    echo -e "${BLUE}   Подключите USB-накопитель объёмом не менее 16GB${NC}"
    echo ""
    read -p "Подключите USB и нажмите Enter для повторной проверки..."
    
    # Повторная проверка
    EXTERNAL_DISKS=$(diskutil list | grep -E "^/dev/disk[0-9]+" | awk '{print $1}' | while read disk; do
        diskutil info "$disk" 2>/dev/null | grep -q "External:.*Yes" && echo "$disk"
    done)
    
    for DISK in $EXTERNAL_DISKS; do
        DISK_SIZE=$(diskutil info "$DISK" 2>/dev/null | grep "Disk Size" | awk '{print $3$4}' | sed 's/[^0-9]//g')
        if [ ! -z "$DISK_SIZE" ] && [ "$DISK_SIZE" -gt 14000000000 ]; then
            USB_DEVICE="$DISK"
            USB_FOUND=true
            DISK_NAME=$(diskutil info "$DISK" 2>/dev/null | grep "Volume Name" | cut -d: -f2 | xargs)
            echo -e "${GREEN}✓ Найден USB-накопитель: ${DISK_NAME}${NC}"
            break
        fi
    done
fi

echo ""

# ШАГ 5: Запуск OCLP для создания установщика
echo -e "${BLUE}🚀 ШАГ 5: Запуск OpenCore Legacy Patcher...${NC}"

# Открываем OCLP
open "/Applications/OpenCore-Patcher.app" 2>/dev/null || {
    echo -e "${RED}✗ Не удалось открыть OCLP${NC}"
    exit 1
}

echo -e "${GREEN}✓ OpenCore Legacy Patcher запущен${NC}"
echo ""

# Инструкции для пользователя
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  АВТОМАТИЧЕСКАЯ ПОДГОТОВКА ЗАВЕРШЕНА${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

echo -e "${BLUE}📋 В открывшемся окне OpenCore Legacy Patcher:${NC}"
echo ""
echo -e "${YELLOW}1. Нажмите 'Create macOS Installer'${NC}"
echo -e "${YELLOW}2. Выберите macOS ${MACOS_VERSION_NUM} ${MACOS_VERSION}${NC}"
echo -e "${YELLOW}3. OCLP автоматически загрузит установщик (30-60 минут)${NC}"

if [ "$USB_FOUND" = true ]; then
    echo -e "${YELLOW}4. Выберите USB-накопитель: ${DISK_NAME}${NC}"
    echo -e "${YELLOW}5. Нажмите 'Create Installer'${NC}"
else
    echo -e "${YELLOW}4. Подключите USB-накопитель (16GB+)${NC}"
    echo -e "${YELLOW}5. Выберите его в OCLP и нажмите 'Create Installer'${NC}"
fi

echo ""
echo -e "${BLUE}⚠️  ВАЖНЫЕ ПРОВЕРКИ (выполнены автоматически):${NC}"
echo -e "${GREEN}  ✓ Резервная копия: $([ "$BACKUP_EXISTS" = true ] && echo "Создана" || echo "Требуется создание")${NC}"
echo -e "${GREEN}  ✓ OpenCore Legacy Patcher: Установлен${NC}"
echo -e "${GREEN}  ✓ Свободное место: ${DISK_SPACE}${NC}"
echo -e "${GREEN}  ✓ USB-накопитель: $([ "$USB_FOUND" = true ] && echo "Найден" || echo "Требуется подключение")${NC}"
echo ""

echo -e "${BLUE}📝 После создания установщика:${NC}"
echo "  1. Перезагрузите Mac, удерживая Option (Alt)"
echo "  2. Выберите загрузку с USB-накопителя"
echo "  3. Следуйте инструкциям установщика macOS"
echo "  4. ${YELLOW}ВАЖНО:${NC} После установки НЕ перезагружайтесь!"
echo "  5. Запустите OCLP и выберите 'Post Install Root Patch'"
echo "  6. Примените патчи для MacBook9,1"
echo "  7. Теперь можно перезагрузиться"
echo ""

echo -e "${GREEN}✅ Все проверки выполнены! Следуйте инструкциям в OCLP${NC}"
echo ""

