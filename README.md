# ZAVhoz Bot - Telegram Bot для управления заявками на ремонт

Асинхронный Telegram-бот для управления заявками на ремонт и работы в образовательной организации. Поддерживает роли: обычные пользователи (сотрудники) и завхоз (администратор).

## ✨ Функциональность

### Для пользователей (сотрудников):
- 📝 Отправка заявок на ремонт с описанием, местоположением, приоритетом и прикреплением фото/документов
- 👁️ Просмотр статуса своих заявок с фильтрацией
- 🔔 Уведомления о изменениях статуса

### Для завхоза:
- 📋 Просмотр открытых заявок с фильтрами
- ✅ Взятие заявок в работу, обновление статуса, добавление комментариев и фото отчетов
- 📁 Архив выполненных заявок с поиском и экспортом в CSV
- 📊 Статистика по заявкам

## 🚀 Быстрый старт

### Требования
- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose (для развертывания)

### Локальная разработка

1. **Клонируйте репозиторий:**
   ```bash
   git clone <repo-url>
   cd zavhoz
   ```

2. **Создайте и активируйте виртуальное окружение:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/macOS
   # или
   venv\Scripts\activate  # Windows
   ```

3. **Установите зависимости:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Скопируйте файл конфигурации:**
   ```bash
   cp .env.example .env
   ```

5. **Заполните переменные окружения в `.env`:**
   ```
   BOT_TOKEN=your_telegram_bot_token
   ADMIN_USER_ID=your_telegram_user_id
   DATABASE_URL=postgresql://zavhoz_user:password@localhost:5432/zavhoz_db
   ```

6. **Создайте таблицы в БД:**
   ```bash
   python database/migrations.py
   ```

7. **Запустите бота:**
   ```bash
   python bot/main.py
   ```

## 📦 Команды разработчика

### Установка зависимостей
```bash
# Базовые зависимости
pip install -e .

# С инструментами разработки
pip install -e ".[dev]"
```

### Лinting и форматирование
```bash
# Проверка с ruff
ruff check .

# Форматирование с black
black .

# Сортировка импортов
isort .

# Все сразу
ruff check . --fix && black . && isort .
```

### Типизация
```bash
# Проверка типов с mypy
mypy . --strict
```

### Тестирование
```bash
# Запуск всех тестов
pytest tests/ -v

# С coverage репортом
pytest tests/ -v --cov=. --cov-report=html

# Только быстрые тесты
pytest tests/ -v -m "not slow"
```

### Безопасность
```bash
# Проверка кода с bandit
bandit -r .

# Проверка зависимостей с safety
safety check
```

### Pre-commit hooks
```bash
# Установка pre-commit
pre-commit install

# Запуск вручную на всех файлах
pre-commit run --all-files
```

## 🐳 Развертывание

### Docker Compose

```bash
# Заполните .env файл
cp .env.example .env
nano .env  # Отредактируйте переменные

# Запустите контейнеры
docker-compose up -d --build

# Проверьте логи
docker-compose logs -f bot

# Остановите
docker-compose down
```

### VPS (Beget и другие)

```bash
# Используйте deploy.sh скрипт
chmod +x deploy.sh
./deploy.sh
```

## 📚 Структура проекта

```
zavhoz/
├── bot/                      # Основной код бота
│   ├── __init__.py
│   └── main.py              # Точка входа
├── database/                # Работа с БД
│   ├── __init__.py
│   ├── connection.py        # Подключение к PostgreSQL
│   └── migrations.py        # Создание таблиц
├── handlers/                # Обработчики команд
│   ├── __init__.py
│   ├── start.py            # /start команда
│   ├── menu.py             # Главное меню
│   ├── create_request.py   # Создание заявок
│   ├── request_actions.py  # Работа с заявками
│   ├── admin.py            # Админ функции
│   └── files.py            # Работа с файлами
├── models/                  # SQLAlchemy модели
│   ├── __init__.py
│   ├── base.py             # Базовый класс
│   ├── user.py             # Модель пользователя
│   ├── request.py          # Модель заявки
│   ├── comment.py          # Модель комментария
│   └── file.py             # Модель файла
├── utils/                   # Вспомогательные функции
│   ├── __init__.py
│   ├── auth.py             # Аутентификация
│   ├── validation.py       # Валидация данных
│   ├── keyboard.py         # Клавиатуры Telegram
│   ├── messages.py         # Текст сообщений
│   ├── notifications.py    # Уведомления
│   └── export.py           # Экспорт в CSV
├── tests/                   # Юнит-тесты
│   ├── __init__.py
│   ├── conftest.py         # Pytest конфиг
│   ├── test_validation.py  # Тесты валидации
│   ├── test_auth.py        # Тесты аутентификации
│   └── ...
├── .github/                 # GitHub Actions CI/CD
│   └── workflows/
│       └── ci.yml          # CI конфиг
├── .env.example            # Пример переменных окружения
├── .gitignore             # Git исключения
├── .pre-commit-config.yaml # Pre-commit конфиг
├── pyproject.toml         # Конфиг проекта и инструментов
├── requirements.txt       # Legacy зависимости
├── docker-compose.yml     # Docker Compose конфиг
├── Dockerfile            # Docker образ
├── deploy.sh            # Скрипт развертывания
├── README.md            # Этот файл
└── CHANGELOG.md         # История изменений
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
pytest

# Конкретный файл
pytest tests/test_validation.py -v

# Конкретный класс
pytest tests/test_validation.py::TestValidateRequestTitle -v

# Конкретный тест
pytest tests/test_validation.py::TestValidateRequestTitle::test_valid_title -v
```

### Coverage

```bash
# HTML отчет (открыть htmlcov/index.html)
pytest --cov=. --cov-report=html

# Terminal отчет
pytest --cov=. --cov-report=term-missing
```

## 🔒 Безопасность

- ✅ SQL injection защита (SQLAlchemy параметризованные запросы)
- ✅ Rate limiting для защиты от спама
- ✅ Валидация входных данных
- ✅ Проверка прав доступа
- ✅ Защита от XSS (санитизация текста)
- ✅ Безопасное хранение переменных окружения
- ✅ Регулярные security аудиты (bandit, safety)

## 📊 Quality Gates

### CI/CD Pipeline

Каждый pull request проходит автоматическую проверку:

1. **Linting**: ruff, black, isort
2. **Type Checking**: mypy (strict mode)
3. **Security**: bandit, safety
4. **Testing**: pytest с coverage ≥80%
5. **Coverage**: codecov

### Status Badge

![CI Status](../../actions/workflows/ci.yml/badge.svg)

## 🤝 Contribution

1. Fork репозиторий
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменений (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📝 Коммиты

Используется [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: добавить новую фичу
fix: исправить баг
docs: обновить документацию
style: форматирование кода
refactor: переделать код без изменения функционала
test: добавить или обновить тесты
chore: обновить зависимости
```

## 📋 Environment Variables

Все переменные окружения описаны в `.env.example`:

| Переменная | Описание | Пример |
|-----------|---------|--------|
| `BOT_TOKEN` | Токен Telegram бота | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` |
| `ADMIN_USER_ID` | Telegram ID администратора | `123456789` |
| `DATABASE_URL` | PostgreSQL URL | `postgresql://user:pass@localhost:5432/db` |
| `LOG_LEVEL` | Уровень логирования | `INFO`, `DEBUG` |
| `ENVIRONMENT` | Окружение | `development`, `production` |

## 🐛 Troubleshooting

### Ошибка подключения к БД
```
DatabaseError: can't connect to server
```
**Решение:**
- Проверьте, что PostgreSQL запущен
- Проверьте URL в переменной `DATABASE_URL`
- Убедитесь, что учетные данные верны

### BOT_TOKEN не найден
```
ValueError: BOT_TOKEN environment variable is not set
```
**Решение:**
- Создайте `.env` файл из `.env.example`
- Заполните `BOT_TOKEN` вашим токеном от BotFather
- Убедитесь, что `.env` находится в корне проекта

### Ошибки типизации
```
error: Call to untyped function "get_user"
```
**Решение:**
- Добавьте type hints ко всем параметрам и возвращаемым значениям
- Запустите `mypy . --strict` для проверки

## 📄 Лицензия

MIT License - see LICENSE file for details

## ✉️ Контакты

- 📧 Email: your.email@example.com
- 💬 Telegram: @yourhandle

## 🙏 Благодарности

- [aiogram](https://github.com/aiogram/aiogram) - Telegram Bot API framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - SQL Toolkit and ORM
- [pytest](https://pytest.org/) - Testing framework