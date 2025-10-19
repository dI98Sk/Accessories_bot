#!/usr/bin/env python3
"""
Скрипт для очистки старых/устаревших файлов проекта
"""
import os
import shutil
from pathlib import Path

# Файлы которые нужно удалить (старая версия)
OLD_FILES = [
    "TelegramBotHandlerUpdate.py",
    "PriceProcessorCR.py",
    "PriceProcessorXtremeCase.py",
    "price_processor_b.py"
]

# Директории для очистки (временные файлы)
CLEAN_DIRS = [
    "temp",
    "__pycache__"
]


def cleanup_old_files():
    """Удаляет старые файлы проекта"""
    print("🧹 Очистка старых файлов...")
    print("=" * 60)
    
    removed_count = 0
    
    # Удаление старых Python файлов
    print("\n📄 Удаление устаревших файлов:")
    for file_name in OLD_FILES:
        file_path = Path(file_name)
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"   ✅ Удален: {file_name}")
                removed_count += 1
            except Exception as e:
                print(f"   ❌ Ошибка при удалении {file_name}: {e}")
        else:
            print(f"   ⏭️  Не найден: {file_name}")
    
    # Очистка временных директорий
    print("\n📁 Очистка временных директорий:")
    for dir_name in CLEAN_DIRS:
        dir_path = Path(dir_name)
        if dir_path.exists() and dir_path.is_dir():
            try:
                shutil.rmtree(dir_path)
                print(f"   ✅ Удалена: {dir_name}/")
                removed_count += 1
            except Exception as e:
                print(f"   ❌ Ошибка при удалении {dir_name}/: {e}")
        else:
            print(f"   ⏭️  Не найдена: {dir_name}/")
    
    print("\n" + "=" * 60)
    if removed_count > 0:
        print(f"✅ Очистка завершена! Удалено элементов: {removed_count}")
    else:
        print("ℹ️  Нечего удалять, все уже чисто!")
    
    print("\n⚠️  ВАЖНО: Старые файлы удалены.")
    print("   Теперь используйте: python channel_monitor_bot.py")


def main():
    """Главная функция"""
    print("⚠️  ВНИМАНИЕ: Этот скрипт удалит старые файлы проекта!")
    print("   Будут удалены:")
    for f in OLD_FILES:
        print(f"   - {f}")
    for d in CLEAN_DIRS:
        print(f"   - {d}/")
    
    response = input("\n❓ Продолжить? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y', 'да', 'д']:
        cleanup_old_files()
    else:
        print("❌ Отменено пользователем")


if __name__ == "__main__":
    main()

