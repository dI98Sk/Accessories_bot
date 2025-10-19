#!/bin/bash
# Быстрая настройка проекта Accessories Bot

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        ACCESSORIES BOT - Быстрая настройка                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Шаг 1: Проверка Python
echo -e "${BLUE}[1/7]${NC} Проверка Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} Python установлен: $PYTHON_VERSION"
else
    echo -e "${RED}✗${NC} Python 3 не найден! Установите Python 3.8+"
    exit 1
fi

# Шаг 2: Создание виртуального окружения
echo ""
echo -e "${BLUE}[2/7]${NC} Настройка виртуального окружения..."
if [ -d "venv" ] || [ -d ".venv" ]; then
    echo -e "${YELLOW}⚠${NC}  Виртуальное окружение уже существует"
else
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Виртуальное окружение создано"
fi

# Активация виртуального окружения
echo "   Активация окружения..."
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi
echo -e "${GREEN}✓${NC} Виртуальное окружение активировано"

# Шаг 3: Установка зависимостей
echo ""
echo -e "${BLUE}[3/7]${NC} Установка зависимостей..."
pip install -q -r requirements.txt
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Зависимости установлены"
else
    echo -e "${RED}✗${NC} Ошибка при установке зависимостей"
    exit 1
fi

# Шаг 4: Создание .env файла
echo ""
echo -e "${BLUE}[4/7]${NC} Настройка конфигурации..."
if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠${NC}  Файл .env уже существует"
    echo "   Текущая конфигурация сохранена"
else
    cp .env .env
    echo -e "${GREEN}✓${NC} Файл .env создан из .env.example"
    echo ""
    echo -e "${YELLOW}⚠ ВАЖНО:${NC} Отредактируйте файл .env и заполните:"
    echo "   - BOT_TOKEN"
    echo "   - SOURCE_CHANNEL_ID"
    echo "   - TARGET_CHANNEL_ID"
    echo ""
    echo "   Откройте: nano .env"
fi

# Шаг 5: Создание необходимых директорий
echo ""
echo -e "${BLUE}[5/7]${NC} Создание рабочих директорий..."
mkdir -p temp
mkdir -p processed_files
mkdir -p logs
echo -e "${GREEN}✓${NC} Директории созданы"

# Шаг 6: Проверка конфигурации
echo ""
echo -e "${BLUE}[6/7]${NC} Проверка конфигурации..."
if python test_config.py &> /dev/null; then
    echo -e "${GREEN}✓${NC} Конфигурация корректна!"
else
    echo -e "${YELLOW}⚠${NC}  Конфигурация требует настройки"
    echo "   Запустите: python test_config.py"
    echo "   для подробной информации"
fi

# Шаг 7: Итоговая информация
echo ""
echo -e "${BLUE}[7/7]${NC} Завершение настройки..."
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    НАСТРОЙКА ЗАВЕРШЕНА                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}✓${NC} Виртуальное окружение: готово"
echo -e "${GREEN}✓${NC} Зависимости: установлены"
echo -e "${GREEN}✓${NC} Конфигурация: создана"
echo -e "${GREEN}✓${NC} Директории: созданы"
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "📋 СЛЕДУЮЩИЕ ШАГИ:"
echo ""
echo "1. Отредактируйте .env файл:"
echo "   ${YELLOW}nano .env${NC}"
echo ""
echo "2. Заполните обязательные параметры:"
echo "   - BOT_TOKEN (от @BotFather)"
echo "   - SOURCE_CHANNEL_ID (канал-источник)"
echo "   - TARGET_CHANNEL_ID (целевой канал)"
echo ""
echo "3. Настройте каналы в Telegram:"
echo "   - Добавьте бота в оба канала как администратора"
echo "   - Получите ID каналов через @getidsbot"
echo ""
echo "4. Проверьте конфигурацию:"
echo "   ${YELLOW}python test_config.py${NC}"
echo ""
echo "5. Запустите бота:"
echo "   ${YELLOW}./start_bot.sh${NC}"
echo "   или"
echo "   ${YELLOW}python channel_monitor_bot.py${NC}"
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "📖 ДОКУМЕНТАЦИЯ:"
echo "   • START_HERE.md    - начните отсюда"
echo "   • SETUP_GUIDE.md   - подробная настройка"
echo "   • README.md        - полная документация"
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}🚀 Готово! Настройте .env и запускайте бота!${NC}"
echo ""

