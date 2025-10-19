"""
Настройка логирования для бота
"""
import logging
import sys
from pathlib import Path
from typing import Optional

from config import AppConfig


def setup_logging(config: Optional[AppConfig] = None) -> logging.Logger:
    """
    Настраивает систему логирования.
    
    Args:
        config: Конфигурация приложения (если None, создается из env)
    
    Returns:
        Корневой логгер
    """
    if config is None:
        config = AppConfig.from_env()
    
    # Создаем директорию для логов если нужно
    log_path = Path(config.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Настройка формата
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Получаем уровень логирования
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Удаляем существующие обработчики
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Обработчик для файла
    file_handler = logging.FileHandler(config.log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(log_format, date_format)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(log_format, date_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Уменьшаем уровень логирования для сторонних библиотек
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openpyxl").setLevel(logging.WARNING)
    
    root_logger.info("=" * 60)
    root_logger.info("Система логирования инициализирована")
    root_logger.info(f"Уровень логирования: {config.log_level}")
    root_logger.info(f"Файл логов: {config.log_file}")
    root_logger.info("=" * 60)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Получает логгер с указанным именем.
    
    Args:
        name: Имя логгера (обычно __name__)
    
    Returns:
        Логгер
    """
    return logging.getLogger(name)

