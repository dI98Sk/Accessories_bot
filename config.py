"""
Конфигурация бота для обработки прайс-листов
"""
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


@dataclass
class TelegramUserConfig:
    """Конфигурация Telegram user client (для чтения каналов)"""
    api_id: int
    api_hash: str
    phone: str
    session_name: str = "user_session"
    
    @classmethod
    def from_env(cls) -> "TelegramUserConfig":
        """Создает конфигурацию из переменных окружения"""
        api_id = os.getenv("TELEGRAM_API_ID")
        if not api_id:
            raise ValueError("TELEGRAM_API_ID не установлен в .env файле")
        
        api_hash = os.getenv("TELEGRAM_API_HASH")
        if not api_hash:
            raise ValueError("TELEGRAM_API_HASH не установлен в .env файле")
        
        phone = os.getenv("TELEGRAM_PHONE")
        if not phone:
            raise ValueError("TELEGRAM_PHONE не установлен в .env файле")
        
        session_name = os.getenv("TELEGRAM_SESSION_NAME", "user_session")
        
        return cls(
            api_id=int(api_id),
            api_hash=api_hash,
            phone=phone,
            session_name=session_name
        )


@dataclass
class BotConfig:
    """Конфигурация Telegram бота (для отправки в канал)"""
    bot_token: str
    target_channel_id: str
    
    @classmethod
    def from_env(cls) -> "BotConfig":
        """Создает конфигурацию из переменных окружения"""
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            raise ValueError("BOT_TOKEN не установлен в .env файле")
        
        target_channel_id = os.getenv("TARGET_CHANNEL_ID")
        if not target_channel_id:
            raise ValueError("TARGET_CHANNEL_ID не установлен в .env файле")
        
        return cls(
            bot_token=bot_token,
            target_channel_id=target_channel_id
        )


@dataclass
class GoogleSheetsConfig:
    """Конфигурация Google Sheets"""
    credentials_file: str
    spreadsheet_id: str
    
    @classmethod
    def from_env(cls, required: bool = True) -> Optional["GoogleSheetsConfig"]:
        """
        Создает конфигурацию из переменных окружения
        
        Args:
            required: Если False, не выбрасывает ошибку при отсутствии параметров
        """
        credentials_file = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "credentials.json")
        spreadsheet_id = os.getenv("CIFROVOY_RAY_SPREADSHEET_ID")
        
        if not required and not spreadsheet_id:
            return None
        
        if not spreadsheet_id:
            raise ValueError("CIFROVOY_RAY_SPREADSHEET_ID не установлен в .env файле")
        
        if not os.path.exists(credentials_file):
            if required:
                raise ValueError(f"Файл credentials не найден: {credentials_file}")
            else:
                return None
        
        return cls(
            credentials_file=credentials_file,
            spreadsheet_id=spreadsheet_id
        )


@dataclass
class DataSourcesConfig:
    """Конфигурация источников данных"""
    enable_xtreme_case: bool
    enable_cifrovoy_ray: bool
    xtreme_case_channel_id: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "DataSourcesConfig":
        """Создает конфигурацию из переменных окружения"""
        enable_xtreme_case = os.getenv("ENABLE_XTREME_CASE", "true").lower() == "true"
        enable_cifrovoy_ray = os.getenv("ENABLE_CIFROVOY_RAY", "false").lower() == "true"
        
        xtreme_case_channel_id = None
        if enable_xtreme_case:
            xtreme_case_channel_id = os.getenv("XTREME_CASE_CHANNEL_ID")
            if not xtreme_case_channel_id:
                raise ValueError("XTREME_CASE_CHANNEL_ID не установлен в .env файле (требуется если ENABLE_XTREME_CASE=true)")
        
        return cls(
            enable_xtreme_case=enable_xtreme_case,
            enable_cifrovoy_ray=enable_cifrovoy_ray,
            xtreme_case_channel_id=xtreme_case_channel_id
        )


@dataclass
class ProcessorConfig:
    """Конфигурация процессора прайсов"""
    markup_value: float
    price_col_index: int = 4
    header_row: int = 5
    output_subdir: str = "processed_files"
    
    @classmethod
    def xtreme_case(cls) -> "ProcessorConfig":
        """Конфигурация для XtremeCase"""
        markup = float(os.getenv("MARKUP_XTREME_CASE", "200"))
        return cls(
            markup_value=markup,
            price_col_index=4,
            header_row=5
        )
    
    @classmethod
    def cifrovoy_ray(cls) -> "ProcessorConfig":
        """Конфигурация для CifrovoyRay"""
        markup = float(os.getenv("MARKUP_CIFROVOY_RAY", "50"))
        return cls(
            markup_value=markup,
            price_col_index=4,
            header_row=5
        )
    
    @classmethod
    def default(cls) -> "ProcessorConfig":
        """Конфигурация по умолчанию"""
        markup = float(os.getenv("MARKUP_DEFAULT", "50"))
        return cls(
            markup_value=markup,
            price_col_index=4,
            header_row=5
        )


@dataclass
class AppConfig:
    """Общая конфигурация приложения"""
    temp_dir: str = "./temp"
    output_dir: str = "./processed_files"
    log_level: str = "INFO"
    log_file: str = "bot.log"
    telegram_check_interval: int = 60
    sheets_check_interval: int = 300
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Создает конфигурацию из переменных окружения"""
        return cls(
            temp_dir=os.getenv("TEMP_DIR", "./temp"),
            output_dir=os.getenv("OUTPUT_DIR", "./processed_files"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE", "bot.log"),
            telegram_check_interval=int(os.getenv("TELEGRAM_CHECK_INTERVAL", "60")),
            sheets_check_interval=int(os.getenv("SHEETS_CHECK_INTERVAL", "300"))
        )


# Глобальные экземпляры конфигураций
def get_telegram_user_config() -> TelegramUserConfig:
    """Получить конфигурацию Telegram user client"""
    return TelegramUserConfig.from_env()


def get_bot_config() -> BotConfig:
    """Получить конфигурацию бота"""
    return BotConfig.from_env()


def get_google_sheets_config(required: bool = True) -> Optional[GoogleSheetsConfig]:
    """Получить конфигурацию Google Sheets"""
    return GoogleSheetsConfig.from_env(required=required)


def get_data_sources_config() -> DataSourcesConfig:
    """Получить конфигурацию источников данных"""
    return DataSourcesConfig.from_env()


def get_app_config() -> AppConfig:
    """Получить конфигурацию приложения"""
    return AppConfig.from_env()

