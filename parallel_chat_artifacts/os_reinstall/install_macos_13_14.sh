#!/bin/bash

# Скрипт для установки macOS 13 (Ventura) или macOS 14 (Sonoma) на MacBook9,1
# ВНИМАНИЕ: MacBook9,1 официально не поддерживает эти версии
# Использование на свой риск!

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Установка macOS 13/14 на MacBook9,1${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Проверка модели
MODEL=$(system_profiler SPHardwareDataType | grep "Model Identifier" | awk '{print $3}')
CURRENT_VERSION=$(sw_vers -productVersion)

echo -e "${BLUE}📋 Информация о системе:${NC}"
echo "  Модель: ${MODEL}"
echo "  Текущая версия: macOS ${CURRENT_VERSION}"
echo ""

if [ "$MODEL" != "MacBook9,1" ]; then
    echo -e "${YELLOW}⚠️  Этот скрипт предназначен для MacBook9,1${NC}"
    echo -e "${YELLOW}   Продолжить? (y/n): ${NC}"
    read -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${RED}⚠️  ВАЖНОЕ ПРЕДУПРЕЖДЕНИЕ:${NC}"
echo -e "${RED}   MacBook9,1 официально НЕ поддерживает macOS 13/14${NC}"
echo -e "${RED}   Установка может привести к нестабильной работе${NC}"
echo -e "${RED}   ОБЯЗАТЕЛЬНО создайте резервную копию перед продолжением!${NC}"
echo ""
read -p "Создали ли вы резервную копию? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}✗ Создайте резервную копию перед продолжением!${NC}"
    echo -e "${BLUE}   Используйте Time Machine или другой метод${NC}"
    exit 1
fi
echo ""

# Выбор версии
echo -e "${BLUE}Выберите версию macOS для установки:${NC}"
echo "1. macOS 13 Ventura"
echo "2. macOS 14 Sonoma"
echo "3. Отмена"
echo ""
read -p "Ваш выбор (1-3): " -n 1 -r
echo ""
echo ""

case $REPLY in
    1)
        MACOS_VERSION="Ventura"
        MACOS_VERSION_NUM="13"
        APP_STORE_ID="1576738294"
        ;;
    2)
        MACOS_VERSION="Sonoma"
        MACOS_VERSION_NUM="14"
        APP_STORE_ID="1576738294"
        ;;
    3)
        echo "Отмена"
        exit 0
        ;;
    *)
        echo -e "${RED}✗ Неверный выбор${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}✓ Выбрана версия: macOS ${MACOS_VERSION_NUM} ${MACOS_VERSION}${NC}"
echo ""

# Метод установки
echo -e "${BLUE}Выберите метод установки:${NC}"
echo "1. Попробовать через App Store (может не работать для неподдерживаемых моделей)"
echo "2. Использовать OpenCore Legacy Patcher (OCLP) - рекомендуется"
echo "3. Создать загрузочный установщик вручную"
echo ""
read -p "Ваш выбор (1-3): " -n 1 -r
echo ""
echo ""

INSTALL_METHOD=$REPLY

case $INSTALL_METHOD in
    1)
        echo -e "${BLUE}📱 Открываю App Store...${NC}"
        open "macappstore://apps.apple.com/app/id${APP_STORE_ID}"
        echo -e "${GREEN}✓ App Store открыт${NC}"
        echo -e "${YELLOW}   Если macOS ${MACOS_VERSION} недоступен, используйте метод 2 (OCLP)${NC}"
        ;;
    2)
        install_with_oclp
        ;;
    3)
        create_installer_manual
        ;;
    *)
        echo -e "${RED}✗ Неверный выбор${NC}"
        exit 1
        ;;
esac

# Функция установки через OCLP
install_with_oclp() {
    echo -e "${BLUE}🔧 Установка через OpenCore Legacy Patcher${NC}"
    echo ""
    echo -e "${YELLOW}Шаги:${NC}"
    echo "1. Загрузите OpenCore Legacy Patcher с официального сайта:"
    echo "   https://github.com/dortania/OpenCore-Legacy-Patcher/releases"
    echo ""
    echo "2. Откройте загруженный .dmg файл"
    echo "3. Запустите OpenCore Legacy Patcher"
    echo "4. Выберите 'Create macOS Installer'"
    echo "5. Выберите macOS ${MACOS_VERSION_NUM} ${MACOS_VERSION}"
    echo "6. Следуйте инструкциям OCLP"
    echo ""
    
    read -p "Открыть страницу загрузки OCLP в браузере? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "https://github.com/dortania/OpenCore-Legacy-Patcher/releases/latest"
    fi
    
    echo ""
    echo -e "${GREEN}✓ Инструкции по OCLP предоставлены${NC}"
    echo -e "${YELLOW}   ВНИМАНИЕ: Следуйте инструкциям OCLP очень внимательно!${NC}"
}

# Функция создания установщика вручную
create_installer_manual() {
    echo -e "${BLUE}📦 Создание загрузочного установщика macOS ${MACOS_VERSION}${NC}"
    echo ""
    echo -e "${YELLOW}Требования:${NC}"
    echo "  • USB-накопитель объёмом не менее 16GB"
    echo "  • Установщик macOS ${MACOS_VERSION} (скачанный через App Store или OCLP)"
    echo ""
    
    read -p "Продолжить создание установщика? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return
    fi
    
    echo ""
    echo -e "${BLUE}Список доступных дисков:${NC}"
    diskutil list external
    echo ""
    read -p "Введите имя или идентификатор USB-накопителя (например, disk2): " USB_DISK
    
    if [ -z "$USB_DISK" ]; then
        echo -e "${RED}✗ Не указан диск${NC}"
        return
    fi
    
    echo ""
    echo -e "${YELLOW}⚠️  ВНИМАНИЕ: Все данные на ${USB_DISK} будут удалены!${NC}"
    read -p "Продолжить? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return
    fi
    
    # Поиск установщика macOS
    INSTALLER_PATH=""
    if [ -d "/Applications/Install macOS ${MACOS_VERSION}.app" ]; then
        INSTALLER_PATH="/Applications/Install macOS ${MACOS_VERSION}.app"
    elif [ -d "/Applications/Install macOS Sonoma.app" ]; then
        INSTALLER_PATH="/Applications/Install macOS Sonoma.app"
    elif [ -d "/Applications/Install macOS Ventura.app" ]; then
        INSTALLER_PATH="/Applications/Install macOS Ventura.app"
    fi
    
    if [ -z "$INSTALLER_PATH" ]; then
        echo -e "${RED}✗ Установщик macOS ${MACOS_VERSION} не найден${NC}"
        echo -e "${YELLOW}   Сначала загрузите установщик через App Store или OCLP${NC}"
        return
    fi
    
    echo -e "${GREEN}✓ Найден установщик: ${INSTALLER_PATH}${NC}"
    echo ""
    echo -e "${BLUE}Создание загрузочного установщика...${NC}"
    echo -e "${YELLOW}   Это может занять 20-30 минут${NC}"
    echo ""
    
    # Создание установщика
    sudo "${INSTALLER_PATH}/Contents/Resources/createinstallmedia" --volume /Volumes/"${USB_DISK}" || {
        echo -e "${RED}✗ Ошибка при создании установщика${NC}"
        echo -e "${YELLOW}   Попробуйте использовать OCLP вместо этого${NC}"
        return
    }
    
    echo ""
    echo -e "${GREEN}✓ Загрузочный установщик создан успешно!${NC}"
    echo ""
    echo -e "${BLUE}Следующие шаги:${NC}"
    echo "1. Перезагрузите Mac, удерживая клавишу Option (Alt)"
    echo "2. Выберите загрузку с USB-накопителя"
    echo "3. Следуйте инструкциям установщика"
    echo ""
}

# Метод уже выполнен выше

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Скрипт завершён${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Дополнительная информация:${NC}"
echo "  • Официальная документация OCLP: https://dortania.github.io/OpenCore-Legacy-Patcher/"
echo "  • Форум поддержки: https://github.com/dortania/OpenCore-Legacy-Patcher/discussions"
echo "  • При проблемах можно вернуться к macOS 12.7.6 через Time Machine"
echo ""

