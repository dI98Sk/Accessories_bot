#!/bin/bash
# Скрипт для запуска Unified Bot

echo "🤖 Запуск Unified Price Bot..."

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "📝 Создайте файл .env на основе .env.example"
    echo "   cp .env.example .env"
    echo "   и заполните необходимые параметры"
    exit 1
fi

# Проверка наличия credentials.json
if [ ! -f credentials.json ]; then
    echo "⚠️  Файл credentials.json не найден!"
    echo "📝 Создайте Service Account в Google Cloud и скачайте JSON ключ"
    echo "   Сохраните его как credentials.json в корне проекта"
    echo ""
    read -p "Продолжить без credentials.json? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Проверка виртуального окружения
if [ ! -d "venv" ]; then
    echo "⚠️  Виртуальное окружение не найдено"
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Установка зависимостей
echo "📦 Проверка зависимостей..."
pip install -q -r requirements.txt

# Запуск бота
echo "🚀 Запуск Unified Price Bot..."
echo "   Мониторинг XtremeCase (Telegram)"
echo "   Мониторинг CifrovoyRay (Google Sheets)"
echo ""
python unified_bot.py

