# mood-sentinel

## Назначение

Mood Sentinel — это система мониторинга настроения и благополучия, которая собирает данные о физическом и эмоциональном состоянии пользователя из различных источников (фитнес-трекеров, мобильных приложений) и предоставляет аналитику через удобные интерфейсы.

Основные возможности:
- Интеграция с фитнес-трекерами и приложениями здоровья
- Анализ паттернов настроения и активности
- Уведомления в Telegram
- Экспорт и визуализация данных
- REST API для интеграции с внешними системами

## Быстрый старт

### Требования
- Python 3.8+
- Docker (опционально)
- Учетная запись Telegram (для уведомлений)

### Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/procop07/mood-sentinel.git
cd mood-sentinel
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройте переменные окружения:
```bash
cp .env.example .env
# Отредактируйте .env файл с вашими настройками
```

5. Запустите приложение:
```bash
python main.py
```

## Экспорт данных из Zepp

### Настройка интеграции с Zepp

1. Войдите в приложение Zepp на мобильном устройстве
2. Перейдите в настройки профиля
3. Найдите раздел "Экспорт данных" или "API доступ"
4. Получите API ключ для доступа к данным

### Конфигурация в приложении

Добавьте в файл `.env`:
```env
ZEPP_API_KEY=your_zepp_api_key
ZEPP_USER_ID=your_user_id
ZEPP_SYNC_INTERVAL=3600  # интервал синхронизации в секундах
```

### Поддерживаемые метрики
- Количество шагов
- Пульс в покое и при активности
- Качество сна
- Уровень стресса
- Калории
- Активные минуты

## Настройка Telegram

### Создание бота

1. Напишите @BotFather в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Сохраните полученный токен

### Получение Chat ID

1. Напишите сообщение вашему боту
2. Перейдите по ссылке: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Найдите `chat.id` в ответе

### Конфигурация

Добавьте в файл `.env`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_NOTIFICATIONS=true
```

### Типы уведомлений
- Daily summary (ежедневная сводка)
- Alert notifications (критические уведомления)
- Weekly reports (еженедельные отчеты)
- Goal achievements (достижение целей)

## Локальный запуск и API

### Запуск в режиме разработки

```bash
# Запуск с горячей перезагрузкой
python -m flask run --debug

# Или через uvicorn для FastAPI
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
# Сборка образа
docker build -t mood-sentinel .

# Запуск контейнера
docker run -d -p 8000:8000 --env-file .env mood-sentinel

# Или через docker-compose
docker-compose up -d
```

### API Endpoints

#### Здоровье и метрики
- `GET /api/v1/health` - статус системы
- `GET /api/v1/metrics` - текущие метрики
- `POST /api/v1/mood` - добавить запись настроения
- `GET /api/v1/mood/history` - история настроения

#### Данные устройств
- `GET /api/v1/devices` - список подключенных устройств
- `POST /api/v1/sync` - принудительная синхронизация
- `GET /api/v1/data/export` - экспорт данных

#### Аутентификация
- `POST /api/v1/auth/login` - вход в систему
- `POST /api/v1/auth/refresh` - обновление токена

### Примеры использования API

```bash
# Получить текущие метрики
curl -X GET "http://localhost:8000/api/v1/metrics" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Добавить запись настроения
curl -X POST "http://localhost:8000/api/v1/mood" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"mood": 7, "note": "Хорошее утро", "timestamp": "2025-01-01T09:00:00Z"}'
```

## CI/CD и артефакты

### GitHub Actions

Проект использует GitHub Actions для автоматизации:

- **Тестирование**: запуск unit и integration тестов
- **Линтинг**: проверка кода с помощью flake8, black, mypy
- **Безопасность**: сканирование зависимостей (safety, bandit)
- **Сборка Docker**: создание и публикация Docker образов
- **Деплой**: автоматический деплой в staging/production

### Конфигурация пайплайна

Основные файлы:
- `.github/workflows/ci.yml` - основной CI пайплайн
- `.github/workflows/deploy.yml` - деплой в production
- `Dockerfile` - сборка приложения
- `docker-compose.yml` - локальная разработка

### Артефакты

- **Docker Images**: `ghcr.io/procop07/mood-sentinel:latest`
- **Test Reports**: покрытие кода и результаты тестов
- **Documentation**: автоматически генерируемая документация API
- **Release Notes**: автоматическое создание changelog

### Переменные окружения для CI/CD

Необходимые секреты в GitHub:
```
DOCKER_USERNAME
DOCKER_PASSWORD
TELEGRAM_BOT_TOKEN
PRODUCTION_SERVER_HOST
PRODUCTION_SSH_KEY
```

## Структура проекта

```
mood-sentinel/
├── src/
│   ├── api/                 # REST API endpoints
│   ├── core/                # Бизнес-логика
│   ├── integrations/        # Интеграции с внешними сервисами
│   │   ├── zepp/           # Интеграция с Zepp
│   │   ├── telegram/       # Telegram бот
│   │   └── health/         # Другие health apps
│   ├── models/             # Модели данных
│   ├── services/           # Сервисы приложения
│   └── utils/              # Утилиты
├── tests/
│   ├── unit/               # Unit тесты
│   ├── integration/        # Интеграционные тесты
│   └── fixtures/           # Тестовые данные
├── config/
│   ├── development.yaml    # Конфигурация для разработки
│   ├── production.yaml     # Конфигурация для production
│   └── logging.yaml        # Настройки логирования
├── docs/                   # Документация
├── scripts/                # Вспомогательные скрипты
├── .github/workflows/      # CI/CD конфигурация
├── docker-compose.yml      # Docker Compose
├── Dockerfile             # Docker образ
├── requirements.txt       # Python зависимости
├── .env.example          # Пример переменных окружения
└── README.md             # Этот файл
```

### Основные компоненты

- **API Layer**: FastAPI/Flask для REST API
- **Data Layer**: SQLAlchemy для работы с БД
- **Integration Layer**: Коннекторы к внешним сервисам
- **Notification Layer**: Система уведомлений
- **Analytics Layer**: Анализ и визуализация данных

## Безопасность и приватность

### Принципы безопасности

1. **Минимизация данных**: Собираем только необходимые данные
2. **Шифрование**: Все sensitive данные шифруются при хранении
3. **Аутентификация**: JWT токены с ротацией
4. **Авторизация**: Role-based access control
5. **Аудит**: Логирование всех операций с данными

### Защита данных

- **Шифрование в покое**: AES-256 для базы данных
- **Шифрование в transit**: TLS 1.3 для всех соединений
- **Хеширование**: bcrypt для паролей
- **Токены**: JWT с коротким временем жизни

### Конфиденциальность

- **Анонимизация**: Возможность анонимизации данных
- **Право на забвение**: API для удаления всех данных пользователя
- **Экспорт данных**: Пользователь может экспортировать свои данные
- **Согласие**: Явное согласие на сбор каждого типа данных

### Переменные окружения для безопасности

```env
# Шифрование
ENCRYPTION_KEY=your-256-bit-encryption-key
JWT_SECRET=your-jwt-secret
JWT_EXPIRY=3600

# База данных
DB_ENCRYPTION=true
DB_BACKUP_ENCRYPTION=true

# Логирование
AUDIT_LOG=true
LOG_RETENTION_DAYS=90

# Безопасность API
RATE_LIMITING=true
CORS_ORIGINS=https://yourdomain.com
```

### Соответствие стандартам

- **GDPR**: Европейский регламент по защите данных
- **HIPAA**: Стандарты для медицинских данных (если применимо)
- **OWASP**: Следование рекомендациям OWASP Top 10
- **SOC 2**: Контроли безопасности и доступности

---

## Лицензия

MIT License - подробности в файле [LICENSE](LICENSE)

## Участие в разработке

Мы приветствуем вклад в проект! См. [CONTRIBUTING.md](CONTRIBUTING.md) для инструкций.

## Поддержка

- 📧 Email: support@mood-sentinel.com
- 💬 Telegram: [@mood_sentinel_support](https://t.me/mood_sentinel_support)
- 🐛 Issues: [GitHub Issues](https://github.com/procop07/mood-sentinel/issues)
- 📚 Документация: [Wiki](https://github.com/procop07/mood-sentinel/wiki)
