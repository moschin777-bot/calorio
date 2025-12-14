#!/bin/bash

# ПОЛНОСТЬЮ АВТОМАТИЧЕСКАЯ НАСТРОЙКА И УСТАНОВКА
# Выполняет все критически важные шаги автоматически

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  ПОЛНАЯ АВТОМАТИЗАЦИЯ УСТАНОВКИ macOS${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Проверка системы
MODEL=$(system_profiler SPHardwareDataType | grep "Model Identifier" | awk '{print $3}')
CURRENT_VERSION=$(sw_vers -productVersion)
DISK_SPACE=$(df -h / | tail -1 | awk '{print $4}')

echo -e "${GREEN}✓ Система: ${MODEL}, macOS ${CURRENT_VERSION}${NC}"
echo -e "${GREEN}✓ Свободное место: ${DISK_SPACE}${NC}"
echo ""

# 1. Настройка резервной копии
echo -e "${BLUE}📋 ШАГ 1: Настройка резервной копии...${NC}"

# Проверка существующих резервных копий
LAST_BACKUP=$(tmutil listbackups 2>/dev/null | tail -1)

if [ ! -z "$LAST_BACKUP" ]; then
    BACKUP_DATE=$(basename "$LAST_BACKUP")
    echo -e "${GREEN}✓ Резервная копия найдена: ${BACKUP_DATE}${NC}"
else
    echo -e "${YELLOW}⚠️  Резервная копия не найдена${NC}"
    echo -e "${BLUE}   Открываю настройки Time Machine...${NC}"
    
    # Открываем настройки Time Machine
    open "x-apple.systempreferences:com.apple.preference.timemachine" 2>/dev/null || \
    open "/System/Library/PreferencePanes/TimeMachine.prefPane" 2>/dev/null || \
    open -b com.apple.systempreferences com.apple.preference.timemachine 2>/dev/null
    
    echo -e "${YELLOW}   Пожалуйста, настройте Time Machine:${NC}"
    echo -e "${YELLOW}   1. Выберите диск для резервного копирования${NC}"
    echo -e "${YELLOW}   2. Включите Time Machine${NC}"
    echo -e "${YELLOW}   3. Дождитесь создания первой резервной копии${NC}"
    echo ""
    echo -e "${BLUE}   Пока Time Machine создаёт резервную копию, продолжаю подготовку...${NC}"
fi

echo ""

# 2. Проверка и установка OCLP
echo -e "${BLUE}📦 ШАГ 2: Проверка OpenCore Legacy Patcher...${NC}"

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

# 3. Подготовка рабочей директории
echo -e "${BLUE}🔧 ШАГ 3: Подготовка рабочей директории...${NC}"

INSTALLER_DIR="$HOME/macos_installer_auto"
mkdir -p "$INSTALLER_DIR"
cd "$INSTALLER_DIR"

echo -e "${GREEN}✓ Рабочая директория: ${INSTALLER_DIR}${NC}"
echo ""

# 4. Создание скрипта для автоматического запуска OCLP
echo -e "${BLUE}🚀 ШАГ 4: Создание автоматического скрипта установки...${NC}"

cat > "$INSTALLER_DIR/auto_oclp_install.sh" << 'OCLP_SCRIPT'
#!/bin/bash

# Автоматический скрипт для OCLP
OCLP_APP="/Applications/OpenCore-Patcher.app"

if [ ! -d "$OCLP_APP" ]; then
    echo "OpenCore Legacy Patcher не найден"
    exit 1
fi

# Запускаем OCLP
open "$OCLP_APP"

echo "OpenCore Legacy Patcher запущен"
echo ""
echo "В открывшемся окне:"
echo "1. Нажмите 'Create macOS Installer'"
echo "2. Выберите macOS 13 Ventura"
echo "3. Дождитесь загрузки установщика (30-60 минут)"
echo "4. Подключите USB-накопитель (16GB+)"
echo "5. Создайте загрузочный установщик"
OCLP_SCRIPT

chmod +x "$INSTALLER_DIR/auto_oclp_install.sh"
echo -e "${GREEN}✓ Скрипт автоматизации создан${NC}"
echo ""

# 5. Проверка всех критических компонентов
echo -e "${BLUE}✅ ШАГ 5: Финальная проверка всех компонентов...${NC}"
echo ""

CHECKS_PASSED=0
CHECKS_TOTAL=5

# Проверка 1: Резервная копия
if [ ! -z "$LAST_BACKUP" ]; then
    echo -e "${GREEN}  ✓ Резервная копия: Создана${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "${YELLOW}  ⚠ Резервная копия: Требуется создание${NC}"
    echo -e "${BLUE}     (Настройки Time Machine открыты)${NC}"
fi

# Проверка 2: OCLP
if [ -d "/Applications/OpenCore-Patcher.app" ]; then
    echo -e "${GREEN}  ✓ OpenCore Legacy Patcher: Установлен${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}  ✗ OpenCore Legacy Patcher: Не установлен${NC}"
fi

# Проверка 3: Свободное место
DISK_SPACE_GB=$(df -g / | tail -1 | awk '{print $4}')
if [ "$DISK_SPACE_GB" -gt 20 ]; then
    echo -e "${GREEN}  ✓ Свободное место: ${DISK_SPACE} (достаточно)${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}  ✗ Свободное место: ${DISK_SPACE} (недостаточно, нужно минимум 20GB)${NC}"
fi

# Проверка 4: Модель Mac
if [ "$MODEL" = "MacBook9,1" ]; then
    echo -e "${GREEN}  ✓ Модель Mac: Поддерживается через OCLP${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "${YELLOW}  ⚠ Модель Mac: ${MODEL} (проверьте совместимость)${NC}"
fi

# Проверка 5: Версия macOS
if [[ "$CURRENT_VERSION" =~ ^12\. ]]; then
    echo -e "${GREEN}  ✓ Текущая версия: macOS ${CURRENT_VERSION} (можно обновить)${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "${YELLOW}  ⚠ Текущая версия: macOS ${CURRENT_VERSION}${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Результат проверки: ${CHECKS_PASSED}/${CHECKS_TOTAL}${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ "$CHECKS_PASSED" -ge 4 ]; then
    echo -e "${GREEN}✅ Система готова к установке macOS 13/14!${NC}"
    echo ""
    
    # Запуск OCLP
    echo -e "${BLUE}🚀 Запускаю OpenCore Legacy Patcher...${NC}"
    sleep 2
    open "/Applications/OpenCore-Patcher.app"
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  ВСЁ ГОТОВО!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}📋 В открывшемся окне OpenCore Legacy Patcher:${NC}"
    echo ""
    echo -e "${YELLOW}1. Нажмите 'Create macOS Installer'${NC}"
    echo -e "${YELLOW}2. Выберите macOS 13 Ventura (рекомендуется)${NC}"
    echo -e "${YELLOW}3. OCLP автоматически загрузит установщик (30-60 минут)${NC}"
    echo -e "${YELLOW}4. Подключите USB-накопитель (16GB+)${NC}"
    echo -e "${YELLOW}5. Выберите USB в OCLP и нажмите 'Create Installer'${NC}"
    echo ""
    echo -e "${BLUE}⚠️  ВАЖНО ПОСЛЕ УСТАНОВКИ macOS:${NC}"
    echo -e "${YELLOW}  • НЕ перезагружайтесь сразу после установки!${NC}"
    echo -e "${YELLOW}  • Запустите OCLP и выберите 'Post Install Root Patch'${NC}"
    echo -e "${YELLOW}  • Примените патчи для MacBook9,1${NC}"
    echo -e "${YELLOW}  • Только после этого перезагрузитесь${NC}"
    echo ""
else
    echo -e "${YELLOW}⚠️  Некоторые проверки не пройдены${NC}"
    echo -e "${YELLOW}   Пожалуйста, исправьте проблемы и запустите скрипт снова${NC}"
    echo ""
    
    if [ -z "$LAST_BACKUP" ]; then
        echo -e "${BLUE}   Особенно важно создать резервную копию!${NC}"
    fi
fi

echo ""
echo -e "${GREEN}✅ Автоматизация завершена!${NC}"

