#!/usr/bin/env python3
"""
Скрипт для тестирования конфигурации бота
"""
import sys
from pathlib import Path

def test_config():
    """Тестирует конфигурацию бота"""
    print("🔍 Проверка конфигурации...")
    print("=" * 60)
    
    # Проверка .env файла
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ Файл .env не найден!")
        print("📝 Создайте файл .env на основе .env:")
        print("   cp .env .env")
        return False
    
    print("✅ Файл .env найден")
    
    # Загрузка конфигурации
    try:
        from config import BotConfig, AppConfig
        
        print("\n📋 Загрузка конфигурации бота...")
        bot_config = BotConfig.from_env()
        
        print(f"   BOT_TOKEN: {bot_config.bot_token[:10]}...{bot_config.bot_token[-5:]}")
        print(f"   SOURCE_CHANNEL_ID: {bot_config.source_channel_id}")
        print(f"   TARGET_CHANNEL_ID: {bot_config.target_channel_id}")
        
        print("\n📋 Загрузка конфигурации приложения...")
        app_config = AppConfig.from_env()
        
        print(f"   TEMP_DIR: {app_config.temp_dir}")
        print(f"   OUTPUT_DIR: {app_config.output_dir}")
        print(f"   LOG_LEVEL: {app_config.log_level}")
        print(f"   LOG_FILE: {app_config.log_file}")
        
        print("\n💰 Конфигурация наценок...")
        from config import ProcessorConfig
        
        xtreme = ProcessorConfig.xtreme_case()
        print(f"   XtremeCase: +{xtreme.markup_value} руб.")
        
        cifrovoy = ProcessorConfig.cifrovoy_ray()
        print(f"   CifrovoyRay: +{cifrovoy.markup_value} руб.")
        
        default = ProcessorConfig.default()
        print(f"   Default: +{default.markup_value} руб.")
        
        print("\n" + "=" * 60)
        print("✅ Конфигурация корректна!")
        print("🚀 Можно запускать бота: python channel_monitor_bot.py")
        return True
        
    except ValueError as e:
        print(f"\n❌ Ошибка конфигурации: {e}")
        print("Проверьте параметры в файле .env")
        return False
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_config()
    sys.exit(0 if success else 1)

