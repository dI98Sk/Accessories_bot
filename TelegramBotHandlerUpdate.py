from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from PriceProcessorXtremeCase import PriceProcessorXtremeCase
from price_processor_b import PriceProcessor

class TelegramBotHandler:
    def __init__(self, token: str, processors: dict):
        """
        processors: словарь вида {"Прайс A": (ProcessorClass, directories_dict)}
        directories_dict: {"Папка 1": "./data1", "Папка 2": "./data2"}
        """
        self.token = token
        self.processors = processors
        self.current_processor = None
        self.current_directories = None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Шаг 1: Выбираем какой прайс обрабатывать
        keyboard = [
            [InlineKeyboardButton(name, callback_data=name)]
            for name in self.processors.keys()
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Выберите прайс для обработки:",
            reply_markup=reply_markup
        )

    async def processor_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        processor_name = query.data
        processor_class, directories = self.processors[processor_name]

        # Создаём объект процессора
        self.current_processor = processor_class()
        self.current_directories = directories

        # Шаг 2: Выбираем директорию
        keyboard = [
            [InlineKeyboardButton(name, callback_data=path)]
            for name, path in directories.items()
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Выберите директорию с файлами для обработки:",
            reply_markup=reply_markup
        )

    async def directory_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        folder_path = query.data
        processed_files = self.current_processor.process_directory(folder_path)

        if not processed_files:
            await query.edit_message_text("Файлы не найдены для обработки в выбранной папке.")
            return

        for file_path in processed_files:
            await query.message.reply_document(document=open(file_path, "rb"), filename=file_path.split("/")[-1])

        await query.edit_message_text("✔ Все файлы обновлены и отправлены.")

        # Сообщение о повторном запуске
        await query.message.reply_text(
            "Обработка завершена. Для нового запуска логики нажмите /start."
        )

    def run(self):
        app = ApplicationBuilder().token(self.token).build()

        # Обработчики
        app.add_handler(CommandHandler("start", self.start))
        # Любой callback мы разделяем по логике:
        # 1. Если processor не выбран → вызываем processor_choice
        # 2. Если processor выбран → вызываем directory_choice
        async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if self.current_processor is None:
                await self.processor_choice(update, context)
            else:
                await self.directory_choice(update, context)

        app.add_handler(CallbackQueryHandler(callback_router))
        print("Бот запущен...")
        app.run_polling()


# === Запуск бота ===
if __name__ == "__main__":
    TOKEN = "8404600376:AAHfOsrZGkYuCiS2A-u9q1oFpHT8RCEuQ6w"

    processors = {
        "PriceProcessorXtremeCase": (PriceProcessorXtremeCase, {"dataXtremeCase": "./dataXtremeCase"}),
        "Прайс B": (PriceProcessor, {"Папка 3": "./data3"})
    }

    bot = TelegramBotHandler(token=TOKEN, processors=processors)
    bot.run()