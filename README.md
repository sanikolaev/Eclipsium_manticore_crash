# Менеджер парсеров

----------------------

Сервис для управления парсерами. Создает задачи по КРОНу, пушит их в кафку, отслеживает
их статусы и отменяет просроченные

## Основной функционал:

- Создание задач для парсеров в зависимости от настроек источников и типов задач
- Отмена "зависших" задач
- Проставление статусов задач

## Алгоритм работы:

Кронтаб дергает 2 ручки:
POST /api/v1/task_group/ -  создание задач
GET /api/v1/task_group/cancel_expired_task_group - отмена просроченных задач

1. По всем зарегистиррованным обработчкикам задач и по всем типам задач создаются группы задач и пушатся в кафку
2. Парсеры потребляют топик, получают задачи, парсят
3. Парсеры отправляют статусы задач в топик task_statuses
4. Парсер менеджер обновляет у задач статусы в зависимости от данных, полученных из кафки
5. Если задача каким-то образом не успела потребится парсером, она отменяется

Реализованы круд методы и контроллеры для основных сущностей:

- Группы задач 
- Задачи
- Источники
- Ассоциативная таблица с источниками

Дополнительно реализованны контроллер словарей

# 1. Установка

## При **первом** запуске необходимо:

Настроить переменные окружения: Создать файл `.env` в корне проекта и указать настройки:

```dotenv
POSTGRES_USER=postgres
POSTGRES_PASSWORD=example
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=postgres

ENVIRONMENT=LOCAL
TEST_SQLALCHEMY_URI="postgresql+asyncpg://postgres:example@localhost:5432/test"
```

### Описание возможных ENV параметров

| Name                          | Description                                                      | Default value          |
|-------------------------------|------------------------------------------------------------------|------------------------|
| `PROJECT_NAME`                | Название проекта                                                 | `parser_manager`       |
| `ENVIRONMENT`                 | Текущее окружение                                                | `PROD`                 |
| `DEFAULT_PAGINATION_SIZE`     | Количество элементов на 1 странице по умолчанию                  | `100`                  |
| `KAFKA_HOST`                  | Хост кафки                                                       | `localhost`            |
| `KAFKA_PORT`                  | Порт кафки                                                       | `9092`                 |
| `KAFKA_MAX_REQUEST_SIZE`      | Максимальный размер сообщения кафки в байтах                     | `1_048_576`            |
| `KAFKA_WORKERS_ENABLED`       | Включены ли кафка воркеры                                        | `true`                 |
| `KAFKA_HEARTBEAT_INTERVAL_MS` | Интервал хертбита кафки в MS                                     | `5_000`                |
| `KAFKA_SESSION_TIMEOUT_MS`    | Длина сессии кафки в MS                                          | `45_000`               |
| `KAFKA_TASKS_CONSUMER_GROUP`  | Группа консюмеров кафки                                          | `parser_manager`       |
| `RSS_PARSER_TASKS_TOPIC`      | Топик для RSS задач                                              | `rss_parser_tasks`     |
| `VK_PARSER_TASKS_TOPIC`       | Топик для VK задач                                               | `vk_parser_tasks`      |
| `YOUTUBE_PARSER_TASKS_TOPIC`  | Топик для YOUTUBE задач                                          | `youtube_parser_tasks` |
| `KAFKA_TASK_STATUS_TOPIC`     | Топик статусов задач. Нужен для обновления данных о задачах в БД | `task_statuses`        |
| `KAFKA_DEFAULT_BULK_SIZE`     | Максимальное количество записей в пачке при потреблении кафки    | `1000`                 |
| `KAFKA_DEFAULT_BULK_TIMEOUT`  | Максимальное время, которое потребляется пачка из кафки. В MS    | `10_000`               |
| `ALCHEMY_POLL_SIZE`           | Размер пула алхимии                                              | `10`                   |
| `ALCHEMY_OVERFLOW_POOL_SIZE`  | Размер оферфлоу пула алхимии                                     | `20`                   |
| `POSTGRES_HOST`               | Хост ПГ                                                          | `None`                 |             
| `POSTGRES_PORT`               | Порт ПГ                                                          | `None`                 |             
| `POSTGRES_USER`               | Юзер ПГ                                                          | `None`                 |             
| `POSTGRES_PASSWORD`           | Пароль ПГ                                                        | `None`                 |             
| `POSTGRES_DB`                 | Имя БД пг                                                        | `None`                 |

# 2. Запуск проекта:

## 2.1. С помощью докера

- `docker compose up` - запуск текущего сервиса;

> флаг `--build` перебилдит текущий проект

## 2.2. Запуск "ручками"

Ставим флаг `poetry config virtualenvs.in-project true`, если хотим создавать .venv в
текущей папки проекта (опционально)

- Устанавливаем зависимости `poetry install`;
- Ставим `pre-commit install` для линта кода;
- Запускаем командой `uvicorn --port 8000 --host 127.0.0.1 app.main:app --reload`

# 3. Использование

## 3.1 Запуск тестов

```bash
pytest --maxfail=1 --cov=app -vv --cov-config .coveragerc
```

```bash
docker compose exec template_service pytest --maxfail=1 --cov=app -vv --cov-config .coveragerc
```

Пропуск "долгих" тестов. Скипнется тест на даунгрейд миграций:

```bash
pytest --maxfail=1 --cov=app -vv --cov-config .coveragerc -m "not slow"
```

## 3.2 Линтеры

Запуск линтеров по всему проекту:

```bash
pre-commit run --all-files
```

## 3.3 Миграции

- `alembic revision --autogenerate -m "message"` - генерация новой миграции
- `alembic upgrade head` - накат миграций
- `alembic -x data=true upgrade head ` - накат миграций вместе с данными. Выполняется
  функция data_upgrades() в файле миграции
- `alembic upgrade head --sql > migration.sql` - генерация SQL файла с миграциями.
- `alembic downgrade -1` - откат миграции на 1 версию назад

# 4. Дополнительная информация
