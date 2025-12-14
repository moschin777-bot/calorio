#!/bin/bash

# Простой скрипт для установки macOS 13 или 14
# Для MacBook9,1 через OpenCore Legacy Patcher

echo "🚀 Установка macOS 13/14 на MacBook9,1"
echo ""

# Проверка модели
MODEL=$(system_profiler SPHardwareDataType | grep "Model Identifier" | awk '{print $3}')
echo "Модель: ${MODEL}"
echo ""

if [ "$MODEL" != "MacBook9,1" ]; then
    echo "⚠️  Этот скрипт для MacBook9,1"
fi

echo "⚠️  ВНИМАНИЕ: MacBook9,1 официально не поддерживает macOS 13/14"
echo "   Используйте OpenCore Legacy Patcher (OCLP)"
echo ""
echo "Выберите версию:"
echo "1. macOS 13 Ventura"
echo "2. macOS 14 Sonoma"
echo ""
read -p "Ваш выбор (1-2): " -n 1 -r
echo ""

case $REPLY in
    1)
        VERSION="Ventura"
        VERSION_NUM="13"
        ;;
    2)
        VERSION="Sonoma"
        VERSION_NUM="14"
        ;;
    *)
        echo "Отмена"
        exit 0
        ;;
esac

echo ""
echo "📥 Открываю страницу загрузки OpenCore Legacy Patcher..."
open "https://github.com/dortania/OpenCore-Legacy-Patcher/releases/latest"

echo ""
echo "📖 Инструкция:"
echo "1. Скачайте последнюю версию OCLP (.dmg файл)"
echo "2. Откройте .dmg и запустите OpenCore Legacy Patcher"
echo "3. Выберите 'Create macOS Installer'"
echo "4. Выберите macOS ${VERSION_NUM} ${VERSION}"
echo "5. Следуйте инструкциям OCLP для установки"
echo ""
echo "📚 Документация: https://dortania.github.io/OpenCore-Legacy-Patcher/"
echo ""
echo "✅ Готово! Следуйте инструкциям OCLP"

