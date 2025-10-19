"""
Unified Bot - объединенный бот для обработки прайс-листов из разных источников
"""
import os
import asyncio
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from telegram import Bot
from telegram.error import TelegramError

from config import (
    get_telegram_user_config,
    get_bot_config,
    get_google_sheets_config,
    get_data_sources_config,
    get_app_config,
    ProcessorConfig
)
from telegram_user_client import TelegramUserReader
from google_sheets_reader import GoogleSheetsReader
from processors import ProcessorFactory
from logger import setup_logging, get_logger

logger = get_logger(__name__)


class UnifiedPriceBot:
    """
    Унифицированный бот для обработки прайс-листов из разных источников:
    - XtremeCase: читается из Telegram канала (user client)
    - CifrovoyRay: читается из Google Sheets
    
    Обработанные файлы отправляются в целевой Telegram канал через бота.
    """
    
    def __init__(self):
        """Инициализирует бота с конфигурацией"""
        logger.info("=" * 80)
        logger.info("UNIFIED PRICE BOT - Инициализация")
        logger.info("=" * 80)
        
        # Загружаем конфигурации
        try:
            self.data_sources_config = get_data_sources_config()
            self.bot_config = get_bot_config()
            self.app_config = get_app_config()
            
            # Загружаем конфигурации источников только если они включены
            self.telegram_user_config = None
            self.google_sheets_config = None
            
            if self.data_sources_config.enable_xtreme_case:
                self.telegram_user_config = get_telegram_user_config()
            
            if self.data_sources_config.enable_cifrovoy_ray:
                self.google_sheets_config = get_google_sheets_config(required=True)
        except ValueError as e:
            logger.error(f"Ошибка конфигурации: {e}")
            raise
        
        # Создаем компоненты
        self.telegram_reader: Optional[TelegramUserReader] = None
        self.sheets_reader: Optional[GoogleSheetsReader] = None
        self.telegram_bot: Optional[Bot] = None
        
        # Статистика
        self.stats = {
            "telegram_files_processed": 0,
            "sheets_files_processed": 0,
            "errors": 0,
            "start_time": None
        }
        
        logger.info("✓ Конфигурация загружена")
    
    async def initialize(self):
        """Инициализирует все компоненты бота"""
        logger.info("\n" + "=" * 80)
        logger.info("Инициализация компонентов...")
        logger.info("=" * 80)
        
        component_num = 1
        total_components = 1  # Telegram Bot всегда нужен
        if self.data_sources_config.enable_xtreme_case:
            total_components += 1
        if self.data_sources_config.enable_cifrovoy_ray:
            total_components += 1
        
        # 1. Telegram User Client (для чтения XtremeCase канала) - если включен
        if self.data_sources_config.enable_xtreme_case:
            logger.info(f"\n[{component_num}/{total_components}] Инициализация Telegram User Client...")
            self.telegram_reader = TelegramUserReader(
                self.telegram_user_config,
                self.data_sources_config,
                self.app_config
            )
            self.telegram_reader.set_file_handler(self._handle_xtreme_case_file)
            await self.telegram_reader.start()
            logger.info("✓ Telegram User Client готов")
            component_num += 1
        else:
            logger.info("\n⏭️  XtremeCase отключен (ENABLE_XTREME_CASE=false)")
            self.telegram_reader = None
        
        # 2. Google Sheets Reader (для чтения CifrovoyRay) - если включен
        if self.data_sources_config.enable_cifrovoy_ray:
            logger.info(f"\n[{component_num}/{total_components}] Инициализация Google Sheets Reader...")
            self.sheets_reader = GoogleSheetsReader(
                self.google_sheets_config,
                self.app_config
            )
            self.sheets_reader.connect()
            self.sheets_reader.set_file_handler(self._handle_cifrovoy_ray_file)
            logger.info("✓ Google Sheets Reader готов")
            component_num += 1
        else:
            logger.info("\n⏭️  CifrovoyRay отключен (ENABLE_CIFROVOY_RAY=false)")
            self.sheets_reader = None
        
        # 3. Telegram Bot (для отправки в целевой канал) - всегда нужен
        logger.info(f"\n[{component_num}/{total_components}] Инициализация Telegram Bot...")
        self.telegram_bot = Bot(token=self.bot_config.bot_token)
        # Проверяем бота
        bot_info = await self.telegram_bot.get_me()
        logger.info(f"✓ Bot готов: @{bot_info.username}")
        
        logger.info("\n" + "=" * 80)
        logger.info("✓ Все активные компоненты инициализированы")
        logger.info("=" * 80 + "\n")
        
        self.stats["start_time"] = datetime.now()
    
    async def _handle_xtreme_case_file(self, file_path: str, file_name: str):
        """
        Обрабатывает файл XtremeCase из Telegram канала.
        
        Args:
            file_path: Путь к скачанному файлу
            file_name: Имя файла
        """
        try:
            logger.info("=" * 80)
            logger.info(f"🔵 ОБРАБОТКА XTREME CASE: {file_name}")
            logger.info("=" * 80)
            
            # Создаем процессор для XtremeCase
            config = ProcessorConfig.xtreme_case()
            processor = ProcessorFactory.create_processor("xtreme_case", config)
            
            logger.info(f"Процессор: {processor.__class__.__name__}")
            logger.info(f"Наценка: +{processor.markup_value} руб.")
            
            # Обрабатываем файл
            processed_file = processor.process_file(file_path)
            
            # Отправляем в целевой канал
            await self._send_to_target_channel(processed_file, file_name, "XtremeCase", processor.markup_value)
            
            # Обновляем статистику
            self.stats["telegram_files_processed"] += 1
            
            # Удаляем временные файлы
            self._cleanup_files(file_path, processed_file)
            
            logger.info(f"✓ {file_name} успешно обработан")
            logger.info("=" * 80 + "\n")
        
        except Exception as e:
            logger.error(f"Ошибка при обработке XtremeCase файла {file_name}: {e}", exc_info=True)
            self.stats["errors"] += 1
    
    async def _handle_cifrovoy_ray_file(self, file_path: str, file_name: str):
        """
        Обрабатывает файл CifrovoyRay из Google Sheets.
        
        Args:
            file_path: Путь к созданному Excel файлу
            file_name: Имя файла
        """
        try:
            logger.info("=" * 80)
            logger.info(f"🟢 ОБРАБОТКА CIFROVOY RAY: {file_name}")
            logger.info("=" * 80)
            
            # Создаем процессор для CifrovoyRay (с разделением листов)
            config = ProcessorConfig.cifrovoy_ray()
            processor = ProcessorFactory.create_processor("cifrovoy_ray", config)
            
            logger.info(f"Процессор: {processor.__class__.__name__}")
            logger.info(f"Наценка: +{processor.markup_value} руб.")
            logger.info("Режим: разделение листов")
            
            # Обрабатываем файл (процессор создаст отдельные файлы для каждого листа)
            processor.process_file(file_path)
            
            # Получаем директорию с обработанными файлами
            input_dir = os.path.dirname(file_path)
            output_dir = os.path.join(input_dir, processor.output_subdir)
            
            # Отправляем все обработанные файлы
            if os.path.exists(output_dir):
                for processed_file_name in os.listdir(output_dir):
                    if processed_file_name.endswith('.xlsx'):
                        processed_file_path = os.path.join(output_dir, processed_file_name)
                        await self._send_to_target_channel(
                            processed_file_path,
                            processed_file_name,
                            "CifrovoyRay",
                            processor.markup_value
                        )
            
            # Обновляем статистику
            self.stats["sheets_files_processed"] += 1
            
            # Удаляем временные файлы
            self._cleanup_files(file_path, output_dir)
            
            logger.info(f"✓ {file_name} успешно обработан")
            logger.info("=" * 80 + "\n")
        
        except Exception as e:
            logger.error(f"Ошибка при обработке CifrovoyRay файла {file_name}: {e}", exc_info=True)
            self.stats["errors"] += 1
    
    async def _send_to_target_channel(self, file_path: str, original_name: str, source_type: str, markup: float):
        """
        Отправляет файл в целевой Telegram канал.
        
        Args:
            file_path: Путь к файлу
            original_name: Оригинальное имя файла
            source_type: Тип источника (XtremeCase/CifrovoyRay)
            markup: Примененная наценка
        """
        try:
            logger.info(f"Отправка в целевой канал: {os.path.basename(file_path)}")
            
            # Формируем caption
            current_time = datetime.now().strftime('%d.%m.%Y %H:%M')
            caption = (
                f"Прайс актуален на {current_time}\n"
                f"{original_name}"
            )
            
            # Отправляем файл
            with open(file_path, 'rb') as f:
                await self.telegram_bot.send_document(
                    chat_id=self.bot_config.target_channel_id,
                    document=f,
                    filename=os.path.basename(file_path),
                    caption=caption
                )
            
            logger.info(f"✓ Файл отправлен в канал")
        
        except TelegramError as e:
            logger.error(f"Ошибка при отправке в Telegram: {e}")
            raise
        except Exception as e:
            logger.error(f"Ошибка при отправке файла: {e}")
            raise
    
    def _cleanup_files(self, *paths):
        """Удаляет временные файлы и директории"""
        for path in paths:
            if not path:
                continue
            
            try:
                path_obj = Path(path)
                if path_obj.is_file():
                    path_obj.unlink()
                    logger.debug(f"Удален файл: {path}")
                elif path_obj.is_dir():
                    import shutil
                    shutil.rmtree(path)
                    logger.debug(f"Удалена директория: {path}")
            except Exception as e:
                logger.warning(f"Не удалось удалить {path}: {e}")
    
    async def start(self):
        """Запускает бота"""
        logger.info("\n" + "🚀" * 40)
        logger.info("UNIFIED PRICE BOT - ЗАПУСК")
        logger.info("🚀" * 40 + "\n")
        
        # Инициализируем компоненты
        await self.initialize()
        
        # Выводим информацию
        logger.info("📊 КОНФИГУРАЦИЯ:")
        logger.info(f"  Целевой канал: {self.bot_config.target_channel_id}")
        
        if self.data_sources_config.enable_xtreme_case:
            logger.info(f"  ✅ XtremeCase: {self.data_sources_config.xtreme_case_channel_id}")
            logger.info(f"     Интервал: {self.app_config.telegram_check_interval} сек")
        else:
            logger.info(f"  ⏭️  XtremeCase: отключен")
        
        if self.data_sources_config.enable_cifrovoy_ray:
            logger.info(f"  ✅ CifrovoyRay: {self.google_sheets_config.spreadsheet_id}")
            logger.info(f"     Интервал: {self.app_config.sheets_check_interval} сек")
        else:
            logger.info(f"  ⏭️  CifrovoyRay: отключен")
        
        logger.info("")
        
        # Обрабатываем последние файлы при первом запуске (опционально)
        process_recent = os.getenv("PROCESS_RECENT_ON_START", "false").lower() == "true"
        if process_recent and self.telegram_reader:
            recent_limit = int(os.getenv("PROCESS_RECENT_LIMIT", "10"))
            logger.info(f"🔄 Обработка последних {recent_limit} файлов из канала...")
            try:
                await self.telegram_reader.process_recent_files(limit=recent_limit)
            except Exception as e:
                logger.error(f"Ошибка при обработке последних файлов: {e}")
        
        # Запускаем мониторинг в параллельных задачах
        logger.info("🔄 Запуск мониторинга активных источников...\n")
        
        tasks = []
        if self.telegram_reader:
            tasks.append(self.telegram_reader.start_monitoring())
        if self.sheets_reader:
            tasks.append(self.sheets_reader.start_monitoring())
        
        if not tasks:
            logger.error("❌ Нет активных источников данных!")
            logger.error("Включите хотя бы один источник в .env файле:")
            logger.error("  ENABLE_XTREME_CASE=true")
            logger.error("  или")
            logger.error("  ENABLE_CIFROVOY_RAY=true")
            return
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("\n⚠️  Остановка по запросу пользователя...")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}", exc_info=True)
        finally:
            await self.stop()
    
    async def stop(self):
        """Останавливает бота"""
        logger.info("\n" + "=" * 80)
        logger.info("Остановка бота...")
        logger.info("=" * 80)
        
        # Выводим статистику
        if self.stats["start_time"]:
            uptime = datetime.now() - self.stats["start_time"]
            hours = int(uptime.total_seconds() // 3600)
            minutes = int((uptime.total_seconds() % 3600) // 60)
            
            logger.info(f"\n📊 СТАТИСТИКА:")
            logger.info(f"  Время работы: {hours}ч {minutes}м")
            logger.info(f"  Обработано из Telegram: {self.stats['telegram_files_processed']}")
            logger.info(f"  Обработано из Sheets: {self.stats['sheets_files_processed']}")
            logger.info(f"  Ошибок: {self.stats['errors']}")
        
        # Останавливаем компоненты
        if self.telegram_reader:
            await self.telegram_reader.stop()
        
        if self.telegram_bot:
            # Telegram Bot не требует явной остановки
            pass
        
        logger.info("\n✓ Бот остановлен")
        logger.info("=" * 80)


def main():
    """Главная функция запуска бота"""
    try:
        # Настраиваем логирование
        app_config = get_app_config()
        setup_logging(app_config)
        
        # Создаем и запускаем бота
        bot = UnifiedPriceBot()
        asyncio.run(bot.start())
        
    except ValueError as e:
        print(f"❌ Ошибка конфигурации: {e}")
        print("Проверьте файл .env и заполните все необходимые параметры")
        return 1
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
        return 0
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())

