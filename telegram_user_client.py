"""
Telegram User Client для чтения каналов от имени пользователя
Использует Telethon для анонимного чтения сообщений
"""
import os
import logging
import asyncio
from pathlib import Path
from typing import Optional, Callable, Awaitable
from datetime import datetime, timedelta, timezone

from telethon import TelegramClient, events
from telethon.tl.types import Message, DocumentAttributeFilename

from config import TelegramUserConfig, DataSourcesConfig, AppConfig
from logger import get_logger

logger = get_logger(__name__)


class TelegramUserReader:
    """
    Клиент для чтения Telegram каналов от имени пользователя.
    Использует Telethon для подключения как user (не бот).
    """
    
    def __init__(
        self,
        user_config: TelegramUserConfig,
        data_sources_config: DataSourcesConfig,
        app_config: AppConfig
    ):
        """
        Args:
            user_config: Конфигурация Telegram user
            data_sources_config: Конфигурация источников данных
            app_config: Конфигурация приложения
        """
        self.user_config = user_config
        self.data_sources_config = data_sources_config
        self.app_config = app_config
        
        # Создаем клиент
        self.client = TelegramClient(
            user_config.session_name,
            user_config.api_id,
            user_config.api_hash
        )
        
        # Обработчик новых файлов
        self.file_handler: Optional[Callable[[str, str], Awaitable[None]]] = None
        
        # Последняя проверенная дата (с timezone для сравнения с Telegram messages)
        self.last_check_time = datetime.now(timezone.utc) - timedelta(days=1)
        
        logger.info("TelegramUserReader инициализирован")
    
    async def start(self):
        """Запускает клиент и выполняет авторизацию"""
        logger.info("Запуск Telegram User Client...")
        
        await self.client.start(phone=self.user_config.phone)
        
        # Проверяем авторизацию
        if await self.client.is_user_authorized():
            me = await self.client.get_me()
            logger.info(f"✓ Авторизован как: {me.first_name} (@{me.username})")
        else:
            logger.error("Не удалось авторизоваться")
            raise RuntimeError("Авторизация не выполнена")
        
        logger.info("✓ Telegram User Client запущен")
    
    async def stop(self):
        """Останавливает клиент"""
        logger.info("Остановка Telegram User Client...")
        await self.client.disconnect()
        logger.info("✓ Telegram User Client остановлен")
    
    def set_file_handler(self, handler: Callable[[str, str], Awaitable[None]]):
        """
        Устанавливает обработчик для новых файлов.
        
        Args:
            handler: Async функция, принимающая (file_path, file_name)
        """
        self.file_handler = handler
        logger.info("Обработчик файлов установлен")
    
    async def check_new_messages(self):
        """Проверяет новые сообщения в канале"""
        try:
            channel_id = self.data_sources_config.xtreme_case_channel_id
            
            # Получаем канал
            try:
                if channel_id.startswith('@'):
                    channel = await self.client.get_entity(channel_id)
                else:
                    channel = await self.client.get_entity(int(channel_id))
            except Exception as e:
                logger.error(f"Не удалось получить канал {channel_id}: {e}")
                return
            
            logger.info(f"📡 Проверка новых сообщений в канале: {channel_id}")
            
            # Получаем новые сообщения
            messages = await self.client.get_messages(
                channel,
                limit=20  # Последние 20 сообщений
            )
            
            logger.info(f"Получено сообщений: {len(messages)}")
            
            new_files_count = 0
            checked_count = 0
            
            for message in messages:
                checked_count += 1
                
                # Проверяем что сообщение новое
                if message.date <= self.last_check_time:
                    logger.debug(f"Сообщение {message.id} старое, пропускаем")
                    continue
                
                logger.info(f"🆕 Найдено новое сообщение ID: {message.id}, дата: {message.date}")
                
                # Проверяем наличие документа
                if message.document:
                    file_name = self._get_document_name(message)
                    
                    # Проверяем что это Excel файл
                    if file_name and file_name.lower().endswith(('.xlsx', '.xls')):
                        logger.info(f"Обнаружен новый файл: {file_name}")
                        
                        # Скачиваем файл
                        file_path = await self._download_file(message, file_name)
                        
                        if file_path and self.file_handler:
                            # Вызываем обработчик
                            try:
                                await self.file_handler(file_path, file_name)
                                new_files_count += 1
                                logger.info(f"✓ Файл {file_name} обработан")
                            except Exception as e:
                                logger.error(f"Ошибка при обработке файла {file_name}: {e}")
            
            # Обновляем время последней проверки (с timezone)
            self.last_check_time = datetime.now(timezone.utc)
            
            if new_files_count > 0:
                logger.info(f"✅ Обработано новых файлов: {new_files_count}")
            else:
                logger.info(f"ℹ️  Новых файлов не найдено (проверено {checked_count} сообщений)")
        
        except Exception as e:
            logger.error(f"Ошибка при проверке новых сообщений: {e}", exc_info=True)
    
    def _get_document_name(self, message: Message) -> Optional[str]:
        """Получает имя файла из сообщения"""
        if not message.document:
            return None
        
        # Ищем атрибут с именем файла
        for attr in message.document.attributes:
            if isinstance(attr, DocumentAttributeFilename):
                return attr.file_name
        
        # Если имя не найдено, используем ID
        return f"document_{message.document.id}.xlsx"
    
    async def _download_file(self, message: Message, file_name: str) -> Optional[str]:
        """
        Скачивает файл из сообщения.
        
        Args:
            message: Сообщение с файлом
            file_name: Имя файла
        
        Returns:
            Путь к скачанному файлу или None при ошибке
        """
        try:
            # Создаем директорию для временных файлов
            temp_dir = Path(self.app_config.temp_dir)
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Генерируем имя файла с временной меткой
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_file_name = f"{timestamp}_{file_name}"
            file_path = temp_dir / safe_file_name
            
            # Скачиваем файл
            logger.info(f"Скачивание файла: {file_name}")
            await self.client.download_media(message.document, file=str(file_path))
            
            logger.info(f"✓ Файл скачан: {file_path}")
            return str(file_path)
        
        except Exception as e:
            logger.error(f"Ошибка при скачивании файла {file_name}: {e}")
            return None
    
    async def process_recent_files(self, limit: int = 10):
        """
        Обрабатывает последние файлы из канала (независимо от даты).
        Полезно для первоначальной загрузки.
        
        Args:
            limit: Сколько последних сообщений проверить
        """
        logger.info(f"🔄 Обработка последних {limit} файлов из канала...")
        
        try:
            channel_id = self.data_sources_config.xtreme_case_channel_id
            
            if channel_id.startswith('@'):
                channel = await self.client.get_entity(channel_id)
            else:
                channel = await self.client.get_entity(int(channel_id))
            
            messages = await self.client.get_messages(channel, limit=limit)
            processed_count = 0
            
            for message in messages:
                if message.document:
                    file_name = self._get_document_name(message)
                    
                    if file_name and file_name.lower().endswith(('.xlsx', '.xls')):
                        logger.info(f"📄 Обнаружен файл: {file_name}")
                        
                        file_path = await self._download_file(message, file_name)
                        
                        if file_path and self.file_handler:
                            try:
                                await self.file_handler(file_path, file_name)
                                processed_count += 1
                            except Exception as e:
                                logger.error(f"Ошибка при обработке файла {file_name}: {e}")
            
            logger.info(f"✅ Обработано файлов из истории: {processed_count}")
            
            # Обновляем время последней проверки
            self.last_check_time = datetime.now(timezone.utc)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке последних файлов: {e}", exc_info=True)
    
    async def start_monitoring(self):
        """
        Запускает мониторинг канала в бесконечном цикле.
        Проверяет новые сообщения с заданным интервалом.
        """
        logger.info("Запуск мониторинга канала...")
        logger.info(f"Интервал проверки: {self.app_config.telegram_check_interval} секунд")
        logger.info(f"Время последней проверки: {self.last_check_time}")
        
        while True:
            try:
                await self.check_new_messages()
                await asyncio.sleep(self.app_config.telegram_check_interval)
            except KeyboardInterrupt:
                logger.info("Мониторинг остановлен пользователем")
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле мониторинга: {e}", exc_info=True)
                await asyncio.sleep(10)  # Ждем перед повтором


async def test_connection():
    """Тестирует подключение к Telegram"""
    from config import get_telegram_user_config, get_data_sources_config, get_app_config
    
    user_config = get_telegram_user_config()
    data_sources_config = get_data_sources_config()
    app_config = get_app_config()
    
    reader = TelegramUserReader(user_config, data_sources_config, app_config)
    
    await reader.start()
    
    # Тест: получаем последние сообщения
    logger.info("Тест: получение последних сообщений...")
    await reader.check_new_messages()
    
    await reader.stop()


if __name__ == "__main__":
    # Настраиваем логирование
    from logger import setup_logging
    setup_logging(get_app_config())
    
    # Запускаем тест
    asyncio.run(test_connection())

