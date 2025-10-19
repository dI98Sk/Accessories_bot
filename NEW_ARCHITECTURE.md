#

 🏗️ Новая архитектура бота - v2.1

## 📋 Обзор изменений

### ✅ Что изменилось

**Версия 2.0** → **Версия 2.1**

#### 1. **XtremeCase**: Чтение через user-аккаунт
**Было:** Бот читал канал как администратор  
**Стало:** User-аккаунт читает канал анонимно через Telethon

**Почему:** Канал не принадлежит нам, нельзя добавить бота как администратора

#### 2. **CifrovoyRay**: Чтение из Google Sheets
**Было:** Чтение из Telegram канала  
**Стало:** Чтение напрямую из Google Таблицы

**Почему:** Прайсы теперь ведутся в Google Sheets

---

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                     UNIFIED PRICE BOT                        │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴──────────┐
                    │                    │
         ┌──────────▼─────────┐ ┌───────▼──────────┐
         │  TelegramUserReader│ │ GoogleSheetsReader│
         │    (Telethon)      │ │    (gspread)      │
         └──────────┬─────────┘ └───────┬──────────┘
                    │                    │
         ┌──────────▼─────────┐ ┌───────▼──────────┐
         │  XtremeCase Channel│ │ CifrovoyRay Sheet │
         │   (чтение как user)│ │  (service account)│
         └──────────┬─────────┘ └───────┬──────────┘
                    │                    │
                    └────────┬───────────┘
                             │
                    ┌────────▼─────────┐
                    │  ProcessorFactory │
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
    ┌─────────▼──────────┐      ┌──────────▼───────────┐
    │ XtremeCaseProcessor│      │CifrovoyRayProcessor  │
    │   (наценка +200)   │      │ (наценка +50, split) │
    └─────────┬──────────┘      └──────────┬───────────┘
              │                             │
              └──────────────┬──────────────┘
                             │
                    ┌────────▼─────────┐
                    │  Telegram Bot    │
                    │ (отправка в канал)│
                    └──────────────────┘
                             │
                    ┌────────▼─────────┐
                    │  Target Channel  │
                    └──────────────────┘
```

---

## 📦 Компоненты

### 1. **TelegramUserReader** (`telegram_user_client.py`)
- Использует **Telethon** для подключения как пользователь
- Читает сообщения из канала XtremeCase анонимно
- Скачивает Excel файлы
- Интервал проверки: настраивается (по умолчанию 60 сек)

### 2. **GoogleSheetsReader** (`google_sheets_reader.py`)
- Использует **gspread** и Google Sheets API
- Читает данные из таблицы CifrovoyRay
- Экспортирует в Excel формат
- Интервал проверки: настраивается (по умолчанию 300 сек)

### 3. **UnifiedPriceBot** (`unified_bot.py`)
- Координирует работу всех компонентов
- Запускает параллельный мониторинг двух источников
- Обрабатывает файлы через процессоры
- Отправляет результаты в целевой канал

### 4. **Processors** (`processors.py`)
- **XtremeCaseProcessor**: наценка +200₽
- **CifrovoyRayProcessor**: наценка +50₽ + разделение листов

---

## ⚙️ Настройка

### Шаг 1: Обновить зависимости

```bash
pip install -r requirements.txt
```

### Шаг 2: Получить Telegram API credentials

1. Перейдите на https://my.telegram.org/apps
2. Войдите с вашим номером телефона
3. Создайте приложение (если еще нет)
4. Скопируйте:
   - `api_id` (число)
   - `api_hash` (строка)

### Шаг 3: Настроить Google Sheets API

#### 3.1. Создать проект в Google Cloud

1. Перейдите на https://console.cloud.google.com/
2. Создайте новый проект
3. Включите **Google Sheets API**:
   - Navigation menu → APIs & Services → Library
   - Найдите "Google Sheets API"
   - Нажмите Enable

#### 3.2. Создать Service Account

1. Navigation menu → IAM & Admin → Service Accounts
2. Нажмите "Create Service Account"
3. Заполните:
   - Name: `price-bot-reader`
   - Description: `Service account for reading price sheets`
4. Нажмите "Create and Continue"
5. Пропустите опциональные шаги
6. Нажмите "Done"

#### 3.3. Получить credentials.json

1. Найдите созданный Service Account в списке
2. Нажмите на него
3. Перейдите на вкладку "Keys"
4. Нажмите "Add Key" → "Create new key"
5. Выберите JSON формат
6. Файл скачается автоматически
7. Переименуйте его в `credentials.json`
8. Поместите в корень проекта

#### 3.4. Дать доступ к таблице

1. Откройте скачанный `credentials.json`
2. Найдите поле `client_email` (например: `price-bot-reader@project-id.iam.gserviceaccount.com`)
3. Откройте вашу Google Таблицу CifrovoyRay
4. Нажмите "Share" (Настроить доступ)
5. Вставьте email из `client_email`
6. Дайте права "Viewer" (Читатель)
7. Нажмите "Send"

#### 3.5. Получить Spreadsheet ID

Из URL таблицы:
```
https://docs.google.com/spreadsheets/d/1abc123def456ghi789/edit
                                      ^^^^^^^^^^^^^^^^^^^
                                      Это и есть ID
```

### Шаг 4: Обновить .env файл

```bash
cp .env .env
nano .env
```

Заполните:

```env
# Telegram User Client (для чтения XtremeCase)
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
TELEGRAM_PHONE=+79991234567
TELEGRAM_SESSION_NAME=user_session

# Telegram Bot (для отправки в целевой канал)
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TARGET_CHANNEL_ID=-1009876543210

# Источники данных
XTREME_CASE_CHANNEL_ID=-1001234567890
# или username: XTREME_CASE_CHANNEL_ID=@channel_name

# Google Sheets
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
CIFROVOY_RAY_SPREADSHEET_ID=1abc123def456ghi789

# Остальное можно оставить по умолчанию
```

### Шаг 5: Первый запуск и авторизация

```bash
python unified_bot.py
```

При первом запуске Telethon попросит:
1. Ввести код из Telegram (придет в "Saved Messages")
2. Возможно, двухфакторную аутентификацию

После авторизации создастся файл `user_session.session` - **не удаляйте его**!

---

## 🚀 Запуск

### Быстрый запуск

```bash
./start_unified_bot.sh
```

### Или напрямую

```bash
python unified_bot.py
```

---

## 📊 Как это работает

### XtremeCase (Telegram)

1. **Каждые 60 секунд** (настраивается):
   - Подключается к каналу как обычный пользователь
   - Проверяет новые сообщения
   - Если есть Excel файл - скачивает
   - Применяет наценку +200₽
   - Отправляет в целевой канал

### CifrovoyRay (Google Sheets)

1. **Каждые 5 минут** (настраивается):
   - Подключается к Google Sheets
   - Экспортирует все листы в Excel
   - Применяет наценку +50₽ к каждому листу
   - Разделяет листы на отдельные файлы
   - Отправляет все файлы в целевой канал

---

## 🔧 Настройка интервалов

В `.env`:

```env
# Как часто проверять Telegram (в секундах)
TELEGRAM_CHECK_INTERVAL=60

# Как часто проверять Google Sheets (в секундах)
SHEETS_CHECK_INTERVAL=300
```

---

## 📝 Логирование

Все операции логируются в `bot.log`:

```bash
# Просмотр в реальном времени
tail -f bot.log

# Последние 100 строк
tail -100 bot.log

# Поиск ошибок
grep ERROR bot.log
```

---

## 🐛 Устранение проблем

### Ошибка: "TELEGRAM_API_ID не установлен"

Заполните `.env` файл с данными от https://my.telegram.org/apps

### Ошибка: "Файл credentials не найден"

1. Создайте Service Account в Google Cloud
2. Скачайте JSON ключ
3. Сохраните как `credentials.json` в корне проекта

### Ошибка: "The user is not a participant of this chat"

Убедитесь что вы (ваш аккаунт) подписаны на канал XtremeCase

### Ошибка: "Insufficient permissions"

Дайте Service Account доступ к Google Таблице (Share → добавить email из credentials.json)

### Бот не видит новые файлы в Telegram

1. Проверьте что вы подписаны на канал
2. Проверьте ID канала (должен начинаться с `-100`)
3. Проверьте логи: `grep "Проверка новых сообщений" bot.log`

---

## 🔐 Безопасность

### Важные файлы (НЕ коммитить в Git!)

- `.env` - настройки
- `credentials.json` - Google API ключ
- `user_session.session` - Telegram сессия
- `*.session-journal` - временные файлы сессии

Все они уже в `.gitignore` ✅

---

## 📈 Мониторинг

### Просмотр статистики

Бот выводит статистику при остановке (Ctrl+C):

```
📊 СТАТИСТИКА:
  Время работы: 2ч 15м
  Обработано из Telegram: 5
  Обработано из Sheets: 3
  Ошибок: 0
```

### Мониторинг в реальном времени

```bash
# В одном терминале
python unified_bot.py

# В другом терминале
tail -f bot.log | grep "✓"
```

---

## 🔄 Миграция с версии 2.0

Старый бот (`channel_monitor_bot.py`) больше не используется.

Используйте теперь:
- `unified_bot.py` - новый главный файл

Старые файлы можно удалить:
- `channel_monitor_bot.py`

---

## 📚 Дополнительные ресурсы

- [Telethon документация](https://docs.telethon.dev/)
- [Google Sheets API](https://developers.google.com/sheets/api)
- [gspread документация](https://docs.gspread.org/)

---

**Версия:** 2.1.0  
**Дата:** 2025-10-19  
**Статус:** ✅ Production Ready

