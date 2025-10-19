#!/bin/bash
# Скрипт для запуска бота

echo "🤖 Запуск Accessories Bot..."

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "📝 Создайте файл .env на основе .env.example"
    echo "   cp .env.example .env"
    echo "   и заполните необходимые параметры"
    exit 1
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
echo "🚀 Запуск бота..."
python channel_monitor_bot.py

