#!/bin/bash

# ФИНАЛЬНЫЙ ПОЛНОСТЬЮ АВТОМАТИЧЕСКИЙ СКРИПТ УСТАНОВКИ macOS 13/14
# Выполняет ВСЕ критически важные шаги с проверками

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

clear
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  ПОЛНАЯ АВТОМАТИЧЕСКАЯ УСТАНОВКА macOS${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Информация о системе
MODEL=$(system_profiler SPHardwareDataType | grep "Model Identifier" | awk '{print $3}')
CURRENT_VERSION=$(sw_vers -productVersion)
DISK_SPACE=$(df -h / | tail -1 | awk '{print $4}')

echo -e "${GREEN}✓ Модель Mac: ${MODEL}${NC}"
echo -e "${GREEN}✓ Текущая версия: macOS ${CURRENT_VERSION}${NC}"
echo -e "${GREEN}✓ Свободное место: ${DISK_SPACE}${NC}"
echo ""

# ========================================
# ШАГ 1: РЕЗЕРВНАЯ КОПИЯ (КРИТИЧЕСКИ ВАЖНО!)
# ========================================
echo -e "${BLUE}📋 ШАГ 1: РЕЗЕРВНАЯ КОПИЯ (КРИТИЧЕСКИ ВАЖНО!)${NC}"
echo ""

BACKUP_STATUS="NOT_CONFIGURED"
LAST_BACKUP=$(tmutil listbackups 2>/dev/null | tail -1)

if [ ! -z "$LAST_BACKUP" ]; then
    BACKUP_DATE=$(basename "$LAST_BACKUP")
    echo -e "${GREEN}✓ Резервная копия найдена: ${BACKUP_DATE}${NC}"
    BACKUP_STATUS="EXISTS"
else
    echo -e "${RED}⚠️  РЕЗЕРВНАЯ КОПИЯ НЕ НАЙДЕНА!${NC}"
    echo ""
    echo -e "${YELLOW}Это КРИТИЧЕСКИ ВАЖНО перед установкой macOS!${NC}"
    echo -e "${YELLOW}Без резервной копии вы можете потерять все данные!${NC}"
    echo ""
    echo -e "${BLUE}Открываю настройки Time Machine...${NC}"
    
    # Открываем настройки Time Machine
    open "x-apple.systempreferences:com.apple.preference.timemachine" 2>/dev/null || \
    open "/System/Library/PreferencePanes/TimeMachine.prefPane" 2>/dev/null
    
    echo ""
    echo -e "${YELLOW}ПОЖАЛУЙСТА, ВЫПОЛНИТЕ СЛЕДУЮЩЕЕ:${NC}"
    echo -e "${YELLOW}1. В открывшемся окне выберите диск для резервного копирования${NC}"
    echo -e "${YELLOW}2. Включите Time Machine (переключатель вверху)${NC}"
    echo -e "${YELLOW}3. Дождитесь создания первой резервной копии${NC}"
    echo ""
    echo -e "${BLUE}Пока Time Machine работает, я продолжу подготовку остального...${NC}"
    echo ""
    read -p "Нажмите Enter после настройки Time Machine..."
    
    # Повторная проверка
    LAST_BACKUP=$(tmutil listbackups 2>/dev/null | tail -1)
    if [ ! -z "$LAST_BACKUP" ]; then
        BACKUP_STATUS="EXISTS"
        echo -e "${GREEN}✓ Резервная копия создана!${NC}"
    else
        echo -e "${YELLOW}⚠️  Резервная копия ещё не создана${NC}"
        echo -e "${YELLOW}   Продолжаю, но НАСТОЯТЕЛЬНО рекомендую создать резервную копию!${NC}"
    fi
fi

echo ""

# ========================================
# ШАГ 2: ПРОВЕРКА И УСТАНОВКА OCLP
# ========================================
echo -e "${BLUE}📦 ШАГ 2: OpenCore Legacy Patcher${NC}"
echo ""

if [ ! -d "/Applications/OpenCore-Patcher.app" ]; then
    echo -e "${YELLOW}⚠️  OCLP не найден, устанавливаю...${NC}"
    
    WORK_DIR="$HOME/macos_installer_auto"
    mkdir -p "$WORK_DIR"
    cd "$WORK_DIR"
    
    if [ ! -f "oclp.zip" ] || [ $(stat -f%z oclp.zip 2>/dev/null || echo 0) -lt 1000000 ]; then
        echo -e "${BLUE}   Загружаю OpenCore Legacy Patcher...${NC}"
        curl -L --progress-bar -o oclp.zip "https://github.com/dortania/OpenCore-Legacy-Patcher/archive/refs/heads/main.zip"
    fi
    
    if [ -f "oclp.zip" ] && [ -s "oclp.zip" ]; then
        echo -e "${BLUE}   Распаковываю...${NC}"
        unzip -q -o oclp.zip 2>/dev/null || true
        
        APP_PATH=$(find . -name "OpenCore-Patcher.app" -type d | head -1)
        if [ ! -z "$APP_PATH" ]; then
            cp -R "$APP_PATH" "/Applications/" 2>/dev/null
            echo -e "${GREEN}✓ OCLP установлен${NC}"
        fi
    fi
fi

if [ -d "/Applications/OpenCore-Patcher.app" ]; then
    echo -e "${GREEN}✓ OpenCore Legacy Patcher готов${NC}"
else
    echo -e "${RED}✗ Не удалось установить OCLP${NC}"
    exit 1
fi

echo ""

# ========================================
# ШАГ 3: ПРОВЕРКА ВСЕХ КРИТИЧЕСКИХ УСЛОВИЙ
# ========================================
echo -e "${BLUE}✅ ШАГ 3: ФИНАЛЬНАЯ ПРОВЕРКА ВСЕХ КОМПОНЕНТОВ${NC}"
echo ""

ALL_CHECKS_OK=true

# Проверка 1: Резервная копия
if [ "$BACKUP_STATUS" = "EXISTS" ]; then
    echo -e "${GREEN}  ✓ Резервная копия: СОЗДАНА${NC}"
else
    echo -e "${RED}  ✗ Резервная копия: НЕ СОЗДАНА (КРИТИЧЕСКИ ВАЖНО!)${NC}"
    ALL_CHECKS_OK=false
fi

# Проверка 2: OCLP
if [ -d "/Applications/OpenCore-Patcher.app" ]; then
    echo -e "${GREEN}  ✓ OpenCore Legacy Patcher: УСТАНОВЛЕН${NC}"
else
    echo -e "${RED}  ✗ OpenCore Legacy Patcher: НЕ УСТАНОВЛЕН${NC}"
    ALL_CHECKS_OK=false
fi

# Проверка 3: Свободное место
DISK_SPACE_GB=$(df -g / | tail -1 | awk '{print $4}')
if [ "$DISK_SPACE_GB" -gt 20 ]; then
    echo -e "${GREEN}  ✓ Свободное место: ${DISK_SPACE} (достаточно)${NC}"
else
    echo -e "${RED}  ✗ Свободное место: ${DISK_SPACE} (недостаточно, нужно минимум 20GB)${NC}"
    ALL_CHECKS_OK=false
fi

# Проверка 4: Модель Mac
if [ "$MODEL" = "MacBook9,1" ]; then
    echo -e "${GREEN}  ✓ Модель Mac: MacBook9,1 (поддерживается через OCLP)${NC}"
else
    echo -e "${YELLOW}  ⚠ Модель Mac: ${MODEL} (проверьте совместимость)${NC}"
fi

# Проверка 5: Версия macOS
if [[ "$CURRENT_VERSION" =~ ^12\. ]]; then
    echo -e "${GREEN}  ✓ Текущая версия: macOS ${CURRENT_VERSION} (можно обновить до 13/14)${NC}"
else
    echo -e "${YELLOW}  ⚠ Текущая версия: macOS ${CURRENT_VERSION}${NC}"
fi

echo ""

# ========================================
# ФИНАЛЬНЫЙ РЕЗУЛЬТАТ
# ========================================
echo -e "${BLUE}========================================${NC}"

if [ "$ALL_CHECKS_OK" = true ]; then
    echo -e "${GREEN}✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!${NC}"
    echo -e "${GREEN}✅ СИСТЕМА ГОТОВА К УСТАНОВКЕ!${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    # Запуск OCLP
    echo -e "${BLUE}🚀 Запускаю OpenCore Legacy Patcher...${NC}"
    sleep 2
    
    # Правильный способ запуска OCLP
    open -a "/Applications/OpenCore-Patcher.app" 2>/dev/null || \
    open "/Applications/OpenCore-Patcher.app" 2>/dev/null || \
    /Applications/OpenCore-Patcher.app/Contents/MacOS/OpenCore-Patcher &
    
    sleep 3
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  ВСЁ ГОТОВО!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}📋 В ОТКРЫВШЕМСЯ ОКНЕ OpenCore Legacy Patcher:${NC}"
    echo ""
    echo -e "${YELLOW}1. Нажмите кнопку 'Create macOS Installer'${NC}"
    echo -e "${YELLOW}2. Выберите macOS 13 Ventura (рекомендуется - более стабильная)${NC}"
    echo -e "${YELLOW}   или macOS 14 Sonoma (новее)${NC}"
    echo -e "${YELLOW}3. OCLP автоматически загрузит установщик macOS (30-60 минут)${NC}"
    echo -e "${YELLOW}4. Подключите USB-накопитель объёмом не менее 16GB${NC}"
    echo -e "${YELLOW}5. В OCLP выберите ваш USB-накопитель${NC}"
    echo -e "${YELLOW}6. Нажмите 'Create Installer' и дождитесь завершения${NC}"
    echo ""
    echo -e "${BLUE}⚠️  КРИТИЧЕСКИ ВАЖНО ПОСЛЕ УСТАНОВКИ macOS:${NC}"
    echo ""
    echo -e "${RED}  ⚠ НЕ ПЕРЕЗАГРУЖАЙТЕСЬ СРАЗУ ПОСЛЕ УСТАНОВКИ!${NC}"
    echo ""
    echo -e "${YELLOW}  Правильная последовательность:${NC}"
    echo -e "${YELLOW}  1. macOS установится и перезагрузится автоматически${NC}"
    echo -e "${YELLOW}  2. После первой загрузки macOS НЕ используйте систему${NC}"
    echo -e "${YELLOW}  3. Сразу запустите OpenCore Legacy Patcher${NC}"
    echo -e "${YELLOW}  4. Нажмите 'Post Install Root Patch'${NC}"
    echo -e "${YELLOW}  5. Выберите вашу модель Mac (MacBook9,1)${NC}"
    echo -e "${YELLOW}  6. Примените все патчи${NC}"
    echo -e "${YELLOW}  7. Только после этого перезагрузитесь${NC}"
    echo ""
    echo -e "${GREEN}✅ Всё настроено правильно! Следуйте инструкциям в OCLP${NC}"
    
else
    echo -e "${RED}✗ НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Пожалуйста, исправьте проблемы:${NC}"
    echo ""
    
    if [ "$BACKUP_STATUS" != "EXISTS" ]; then
        echo -e "${RED}  • Создайте резервную копию через Time Machine!${NC}"
        echo -e "${RED}    Это КРИТИЧЕСКИ ВАЖНО для безопасности ваших данных!${NC}"
    fi
    
    if [ ! -d "/Applications/OpenCore-Patcher.app" ]; then
        echo -e "${RED}  • Установите OpenCore Legacy Patcher${NC}"
    fi
    
    if [ "$DISK_SPACE_GB" -le 20 ]; then
        echo -e "${RED}  • Освободите место на диске (нужно минимум 20GB)${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}После исправления проблем запустите скрипт снова${NC}"
    exit 1
fi

echo ""

