# ОСЬ — тестовое задание (Backend Trainee · Python / FastAPI)

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063)](https://docs.pydantic.dev/)
[![Tests](https://img.shields.io/badge/Tests-pytest-2E7D32)](https://pytest.org/)
[![Build](https://github.com/GolrovKirill/Test_Task_OS/actions/workflows/ci.yml/badge.svg)](https://github.com/GolrovKirill/Test_Task_OS/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> REST API бронирования столика в ресторане. Одна дата + одно время — один
> активный заказ: повторная бронь занятого слота получает `409`, отменённая
> бронь слот освобождает. Swagger доступен на `/docs` без настройки.

## Стек

- Python 3.11+, FastAPI, Pydantic v2 (валидация `422` из коробки)
- Хранение в памяти за интерфейсом репозитория (см. «Решения»)
- pytest + TestClient, ruff, GitHub Actions CI

## Быстрый старт

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
./scripts/run.sh
```

API: http://127.0.0.1:8000 · Swagger: http://127.0.0.1:8000/docs

Проверка:

```bash
curl -s http://127.0.0.1:8000/health
```

Примеры запросов:

```bash
# Создать бронь → 201
curl -s -X POST http://127.0.0.1:8000/bookings \
  -H 'Content-Type: application/json' \
  -d '{"name":"Иван Петров","phone":"+71234567890","booking_date":"2026-12-15","booking_time":"18:00","guests":2}'

# Повторная бронь того же слота → 409 {"detail": "Slot is already booked"}
curl -s -X POST http://127.0.0.1:8000/bookings \
  -H 'Content-Type: application/json' \
  -d '{"name":"Анна Смирнова","phone":"+79876543210","booking_date":"2026-12-15","booking_time":"18:00","guests":3}'

# Список с фильтром по дате
curl -s 'http://127.0.0.1:8000/bookings?date=2026-12-15'

# Отменить бронь → 200, статус становится cancelled
curl -s -X DELETE http://127.0.0.1:8000/bookings/1
```

## API

| Метод   | Маршрут          | Описание                                                        |
|---------|------------------|-----------------------------------------------------------------|
| POST    | `/bookings`      | Создать бронь → `201`; слот занят → `409`                       |
| GET     | `/bookings`      | Список броней, необязательный фильтр `?date=YYYY-MM-DD`         |
| GET     | `/bookings/{id}` | Бронь по id → `200`; не найдена → `404`                         |
| DELETE  | `/bookings/{id}` | Отменить: статус → `cancelled`, запись остаётся → `200`         |
| GET     | `/health`        | Проверка живости                                                |

Правила валидации (нарушение → стандартный `422`):

| Поле           | Правило                                         |
|----------------|-------------------------------------------------|
| `name`         | 2–50 символов                                   |
| `phone`        | `+7` + ровно 10 цифр                            |
| `booking_date` | не в прошлом и не дальше 30 дней                |
| `booking_time` | целый час с 12:00 до 22:00 включительно         |
| `guests`       | 1–10                                            |

Коды ошибок:

| Ситуация           | Код | Ответ                                    |
|--------------------|-----|------------------------------------------|
| Бронь создана      | 201 | Бронь со `status=active`                 |
| Невалидные данные  | 422 | Стандартный ответ валидации FastAPI      |
| Бронь не найдена   | 404 | `{"detail": "Booking not found"}`        |
| Слот уже занят     | 409 | `{"detail": "Slot is already booked"}`   |
| Бронь отменена     | 200 | Бронь со `status=cancelled`              |

## Тесты

```bash
./scripts/test.sh              # все тесты
./scripts/test.sh -k conflict  # по имени
```

Покрыты ключевые правила: главное правило «один активный слот», освобождение
слота после отмены, 404/409/422, фильтр по дате, идемпотентность отмены.

## Структура проекта

```
src/booking_api/
├── api/                 # HTTP-слой: роуты, обработчики ошибок, DI
│   ├── routers/bookings.py
│   ├── exceptions.py    # доменные ошибки → HTTP-ответы
│   └── deps.py
├── domain/              # сущность, статусы, доменные ошибки (без фреймворков)
├── services/            # бизнес-правила: сервис бронирования
├── infrastructure/      # репозиторий (интерфейс + in-memory реализация)
├── schemas/             # Pydantic v2 схемы запроса/ответа
└── main.py              # фабрика приложения
tests/                   # pytest + TestClient
scripts/                 # run.sh, test.sh
```

## Решения и почему

1. **Слои `api → services → infrastructure`, отдельно `domain` и `schemas`.**
   Роуты остаются тонкими, а правила (занятость слота, отмена) живут в сервисе
   и тестируются без HTTP.
2. **Валидация полей — в Pydantic v2.** Ограничения и бизнес-правила даты/времени
   объявлены в схемах, поэтому все нарушения автоматически дают стандартный `422`.
3. **Доменные исключения + один обработчик в API.** Домен не знает про HTTP,
   а коды 404/409 и тексты `detail` заданы в одном месте — ровно как в задании.
4. **Хранение в памяти за интерфейсом репозитория.** По условию на оценку не
   влияет, а замена на SQLite/SQLAlchemy не потребует менять сервис или API.
5. **`create_app()` как фабрика.** Каждый тест получает приложение с чистой
   памятью — тесты изолированы друг от друга.

## Что доделал бы при наличии времени

- SQLite через SQLAlchemy за тем же интерфейсом репозитория + фикстура БД в тестах
- Проверку уникальности слота прямо на уровне хранилища (составной индекс)
- Пагинацию списка и фильтр по статусу, контейнеризацию для единого окружения
