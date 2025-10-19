"""
Telegram бот для мониторинга канала и автоматической обработки прайс-листов
"""
import os
import asyncio
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from telegram import Update, Document
from telegram.ext import (
    Application,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler
)

from config import BotConfig, AppConfig
from processors import ProcessorFactory
from logger import setup_logging, get_logger

logger = get_logger(__name__)


class ChannelMonitorBot:
    """
    Бот для мониторинга канала-источника и автоматической обработки прайс-листов.
    
    Функциональность:
    - Мониторит канал-источник на наличие новых Excel файлов
    - Автоматически определяет тип прайса
    - Обрабатывает файл с соответствующей наценкой
    - Отправляет результат в целевой канал
    """
    
    def __init__(self, bot_config: BotConfig, app_config: AppConfig):
        """
        Args:
            bot_config: Конфигурация бота
            app_config: Конфигурация приложения
        """
        self.bot_config = bot_config
        self.app_config = app_config
        
        # Создаем необходимые директории
        Path(app_config.temp_dir).mkdir(parents=True, exist_ok=True)
        Path(app_config.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Статистика
        self.stats = {
            "processed_files": 0,
            "errors": 0,
            "start_time": None
        }
        
        logger.info("ChannelMonitorBot инициализирован")
        logger.info(f"Канал-источник: {bot_config.source_channel_id}")
        logger.info(f"Целевой канал: {bot_config.target_channel_id}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        if update.effective_chat.id != int(self.bot_config.source_channel_id):
            await update.message.reply_text(
                "⚠️ Этот бот работает только в настроенном канале-источнике."
            )
            return
        
        await update.message.reply_text(
            "✅ Бот активен и мониторит канал.\n"
            "📊 Отправьте Excel файл с прайсом для автоматической обработки."
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /stats - показывает статистику"""
        uptime = "N/A"
        if self.stats["start_time"]:
            uptime_seconds = (datetime.now() - self.stats["start_time"]).total_seconds()
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            uptime = f"{hours}ч {minutes}м"
        
        stats_text = (
            "📊 **Статистика бота**\n\n"
            f"⏱ Время работы: {uptime}\n"
            f"✅ Обработано файлов: {self.stats['processed_files']}\n"
            f"❌ Ошибок: {self.stats['errors']}\n"
        )
        
        await update.message.reply_text(stats_text)
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик документов (Excel файлов) из канала-источника.
        """
        # Проверяем, что сообщение из канала-источника
        chat_id = str(update.effective_chat.id)
        source_id = self.bot_config.source_channel_id.replace("@", "")
        
        logger.info(f"Получен документ из чата: {chat_id}")
        
        # Получаем документ
        document: Document = update.message.document
        
        # Проверяем, что это Excel файл
        if not document.file_name.lower().endswith(('.xlsx', '.xls')):
            logger.info(f"Файл {document.file_name} не является Excel файлом, пропускаем")
            return
        
        try:
            logger.info(f"Начало обработки файла: {document.file_name}")
            
            # Скачиваем файл
            file = await context.bot.get_file(document.file_id)
            temp_file_path = os.path.join(
                self.app_config.temp_dir,
                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{document.file_name}"
            )
            await file.download_to_drive(temp_file_path)
            logger.info(f"Файл скачан: {temp_file_path}")
            
            # Автоматически определяем тип и создаем процессор
            processor = ProcessorFactory.auto_create_processor(temp_file_path)
            logger.info(f"Создан процессор: {processor.__class__.__name__}")
            logger.info(f"Наценка: {processor.markup_value}")
            
            # Обрабатываем файл
            processed_file = processor.process_file(temp_file_path)
            logger.info(f"Файл обработан: {processed_file}")
            
            # Отправляем в целевой канал
            with open(processed_file, 'rb') as f:
                caption = (
                    f"✅ Прайс обработан\n"
                    f"📄 Исходный файл: {document.file_name}\n"
                    f"💰 Наценка: +{processor.markup_value} руб.\n"
                    f"🕐 Время обработки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
                await context.bot.send_document(
                    chat_id=self.bot_config.target_channel_id,
                    document=f,
                    filename=os.path.basename(processed_file),
                    caption=caption
                )
            
            logger.info(f"✔ Файл отправлен в целевой канал: {os.path.basename(processed_file)}")
            
            # Обновляем статистику
            self.stats["processed_files"] += 1
            
            # Удаляем временные файлы
            try:
                os.remove(temp_file_path)
                if os.path.exists(processed_file):
                    os.remove(processed_file)
                logger.debug("Временные файлы удалены")
            except Exception as e:
                logger.warning(f"Не удалось удалить временные файлы: {e}")
            
            # Отправляем подтверждение в канал-источник (опционально)
            if update.message:
                await update.message.reply_text(
                    f"✅ Файл '{document.file_name}' успешно обработан и отправлен!"
                )
        
        except Exception as e:
            logger.error(f"Ошибка при обработке файла {document.file_name}: {e}", exc_info=True)
            self.stats["errors"] += 1
            
            # Уведомляем об ошибке
            if update.message:
                await update.message.reply_text(
                    f"❌ Ошибка при обработке файла '{document.file_name}':\n{str(e)}"
                )
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error("Произошла ошибка при обработке обновления:", exc_info=context.error)
        self.stats["errors"] += 1
    
    def run(self):
        """Запускает бота"""
        logger.info("Запуск бота...")
        
        # Создаем приложение
        application = Application.builder().token(self.bot_config.bot_token).build()
        
        # Регистрируем обработчики команд
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        
        # Регистрируем обработчик документов
        application.add_handler(
            MessageHandler(filters.Document.ALL, self.handle_document)
        )
        
        # Регистрируем обработчик ошибок
        application.add_error_handler(self.error_handler)
        
        # Запускаем статистику
        self.stats["start_time"] = datetime.now()
        
        logger.info("🚀 Бот запущен и готов к работе!")
        logger.info("Мониторинг канала начат...")
        
        # Запускаем polling
        application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Главная функция запуска бота"""
    try:
        # Настраиваем логирование
        app_config = AppConfig.from_env()
        setup_logging(app_config)
        
        # Загружаем конфигурацию
        bot_config = BotConfig.from_env()
        
        # Создаем и запускаем бота
        bot = ChannelMonitorBot(bot_config, app_config)
        bot.run()
        
    except ValueError as e:
        print(f"❌ Ошибка конфигурации: {e}")
        print("Пожалуйста, проверьте файл .env")
        return 1
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
        return 0
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())

