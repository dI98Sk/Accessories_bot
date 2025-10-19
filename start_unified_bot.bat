@echo off
REM Скрипт для запуска Unified Bot на Windows

echo ====================================================================
echo            Запуск Unified Price Bot (Windows)
echo ====================================================================
echo.

REM Проверка наличия .env файла
if not exist .env (
    echo [ERROR] Файл .env не найден!
    echo.
    echo Создайте файл .env на основе .env.example:
    echo    copy .env.example .env
    echo    notepad .env
    echo.
    pause
    exit /b 1
)

REM Проверка виртуального окружения
if not exist venv\ (
    echo [INFO] Виртуальное окружение не найдено
    echo [INFO] Создание виртуального окружения...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Не удалось создать виртуальное окружение
        pause
        exit /b 1
    )
)

REM Активация виртуального окружения
echo [INFO] Активация виртуального окружения...
call venv\Scripts\activate.bat

REM Проверка активации
if not defined VIRTUAL_ENV (
    echo [WARNING] Виртуальное окружение не активировано
    echo [INFO] Пытаемся использовать системный Python...
)

REM Установка зависимостей
echo [INFO] Проверка зависимостей...
python -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Ошибка при установке зависимостей
    pause
    exit /b 1
)

REM Запуск бота
echo.
echo ====================================================================
echo            Запуск Unified Price Bot
echo ====================================================================
echo.
echo Мониторинг XtremeCase (Telegram) - каждые 3 часа
echo.
python unified_bot.py

pause

