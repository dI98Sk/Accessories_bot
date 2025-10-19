#!/usr/bin/env python3
"""
Прямой запуск бота без скриптов.
Работает на любой платформе (Mac, Linux, Windows).
"""
import sys
import os
import subprocess

def check_dependencies():
    """Проверяет что все зависимости установлены"""
    print("🔍 Проверка зависимостей...")
    
    required_packages = [
        'telegram',
        'telethon', 
        'gspread',
        'openpyxl',
        'dotenv'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Не хватает зависимостей: {', '.join(missing)}")
        print()
        print("Установите их:")
        print(f"  python -m pip install -r requirements.txt")
        print()
        print("Или установите напрямую:")
        print(f"  python -m pip install python-telegram-bot telethon gspread openpyxl python-dotenv")
        return False
    
    print("✅ Все зависимости установлены")
    return True


def check_env_file():
    """Проверяет наличие .env файла"""
    print("🔍 Проверка конфигурации...")
    
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден!")
        print()
        print("Создайте его:")
        
        if os.name == 'nt':  # Windows
            print("  copy .env.example .env")
            print("  notepad .env")
        else:  # Mac/Linux
            print("  cp .env.example .env")
            print("  nano .env")
        
        return False
    
    print("✅ Файл .env найден")
    return True


def main():
    """Главная функция"""
    print("╔════════════════════════════════════════════════════════════╗")
    print("║           UNIFIED PRICE BOT - Прямой запуск               ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    # Проверка .env
    if not check_env_file():
        input("\nНажмите Enter для выхода...")
        return 1
    
    print()
    
    # Проверка зависимостей
    if not check_dependencies():
        print()
        response = input("Установить зависимости сейчас? (y/n): ").strip().lower()
        if response in ['y', 'yes', 'д', 'да']:
            print("\n📦 Установка зависимостей...")
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
                capture_output=False
            )
            if result.returncode != 0:
                print("\n❌ Ошибка при установке зависимостей")
                input("\nНажмите Enter для выхода...")
                return 1
            print("✅ Зависимости установлены")
        else:
            input("\nНажмите Enter для выхода...")
            return 1
    
    print()
    print("════════════════════════════════════════════════════════════")
    print("🚀 Запуск бота...")
    print("════════════════════════════════════════════════════════════")
    print()
    
    # Запуск главного бота
    try:
        from unified_bot import main as bot_main
        return bot_main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Бот остановлен пользователем")
        return 0
    except Exception as e:
        print(f"\n❌ Ошибка при запуске: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")
        return 1


if __name__ == "__main__":
    exit(main())

