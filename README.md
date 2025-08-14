# Микросервисные FastAPI-приложения для управления и контроля бизнеса(Business process management)

Проект теперь состоит из четырех микросервисов:

- **User Service** (порт 8001) - управление пользователями, статусами доступа, привязка к командам
- **Team Service** (порт 8002) - управление командами, организационной структурой, новостями
- **Task Service** (порт 8003) - управление задачами, комментариями, оценками, встречами, производительностью
- **Calendar Service** (порт 8004) - управление календарем, проверка доступности времени

### User Service

- ✅ Статусы доступа пользователей (active, inactive, suspended, pending)
- ✅ Роли пользователей (user, admin, team_admin, manager)
- ✅ Обновление и удаление пользователей
- ✅ Привязка к командам при регистрации
- ✅ Управление статусами пользователей

### Team Service

- ✅ Полная организационная структура с иерархией
- ✅ Управление участниками подразделений
- ✅ Система новостей команд
- ✅ CRUD операции для всех сущностей

### Task Service

- ✅ Статусы выполнения задач (created, in_progress, review, completed, cancelled)
- ✅ Приоритеты задач (low, medium, high, urgent)
- ✅ Отслеживание времени выполнения
- ✅ Система оценки производительности
- ✅ Расширенная система встреч

### Calendar Service

- ✅ Управление событиями календаря
- ✅ Проверка доступности времени
- ✅ Настройки рабочего времени пользователей
- ✅ Интеграция с задачами и встречами

## Гайд по запуску и тестированию микросервисов:

1. Подготовка:

* Клонировать репозиторий

```sh
cd bpm-microservices
```

* Сборка и запуск всех микросервисов(миграция применится автоматически)

```sh
docker-compose up -d --build
```

* Проверка доступности:

- User Service: http://localhost:8001/docs
- Team Service: http://localhost:8002/docs
- Task Service: http://localhost:8003/docs
- Calendar Service: http://localhost:8004/docs
- RabbitMQ Management: http://localhost:15672 (admin/admin)

2. Тестирование функционала:

### 1. User Service

#### 1.1 Регистрация пользователя

```bash
curl -X POST "http://localhost:8001/api/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "securepassword123",
    "name": "John Doe",
    "phone": "+1234567890",
    "position": "Senior Developer",
    "department": "Engineering"
  }'
```

#### 1.2 Регистрация с кодом приглашения

```bash
curl -X POST "http://localhost:8001/api/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jane.smith@example.com",
    "password": "securepassword456",
    "name": "Jane Smith",
    "invite_code": "AbC123Xy",
    "phone": "+1234567891",
    "position": "Product Manager",
    "department": "Product"
  }'
```

#### 1.3 Обновление пользователя

```bash
curl -X PUT "http://localhost:8001/api/users/1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Updated Doe",
    "phone": "+1234567899",
    "position": "Lead Developer"
  }'
```

#### 1.4 Изменение статуса пользователя

```bash
curl -X PUT "http://localhost:8001/api/users/1/status" \
  -H "Content-Type: application/json" \
  -d '"suspended"'
```

#### 1.5 Назначение в команду

```bash
curl -X PUT "http://localhost:8001/api/users/1/team" \
  -H "Content-Type: application/json" \
  -d '1'
```

### 2. Team Service

#### 2.1 Создание команды с описанием

```bash
curl -X POST "http://localhost:8002/api/teams" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Команда разработки",
    "description": "Основная команда разработки продукта",
    "owner_id": 1
  }'
```

#### 2.2 Создание иерархической структуры

```bash
# Создание главного подразделения
curl -X POST "http://localhost:8002/api/org_units" \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": 1,
    "name": "Отдел разработки",
    "description": "Главный отдел разработки"
  }'

# Создание подразделения-потомка
curl -X POST "http://localhost:8002/api/org_units" \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": 1,
    "name": "Frontend команда",
    "description": "Команда фронтенд разработки",
    "parent_id": 1
  }'
```

#### 2.3 Добавление участников с ролями

```bash
curl -X POST "http://localhost:8002/api/org_members" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "org_unit_id": 2,
    "position": "Senior Frontend Developer",
    "manager_id": null
  }'
```

#### 2.4 Создание новости команды

```bash
curl -X POST "http://localhost:8002/api/news" \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": 1,
    "author_id": 1,
    "title": "Новый релиз v2.0",
    "content": "Мы успешно выпустили новую версию продукта с множеством улучшений!"
  }'
```

### 3. Task Service

#### 3.1 Создание задачи с приоритетом

```bash
curl -X POST "http://localhost:8003/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Критический баг в авторизации",
    "description": "Необходимо исправить баг с авторизацией пользователей",
    "creator_id": 1,
    "assignee_id": 1,
    "team_id": 1,
    "org_unit_id": 2,
    "priority": 1,
    "due_at": "2024-01-20T18:00:00Z",
    "estimated_hours": 4.0
  }'
```

#### 3.2 Обновление статуса задачи

```bash
curl -X PUT "http://localhost:8003/api/tasks/1" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "started_at": "2024-01-15T09:00:00Z"
  }'
```

#### 3.3 Завершение задачи

```bash
curl -X PUT "http://localhost:8003/api/tasks/1" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "completed_at": "2024-01-15T17:00:00Z",
    "actual_hours": 6.5
  }'
```

#### 3.4 Оценка задачи с обратной связью

```bash
curl -X POST "http://localhost:8003/api/tasks/1/evaluate" \
  -H "Content-Type: application/json" \
  -d '{
      "качество_кода": 4,
      "соблюдение_сроков": 3,
      "документация": 5,
      "тестирование": 4
    },
    "feedback": "Отличная работа! Код качественный, но немного задержались со сроками."
  }'
```

### 4. Calendar Service

#### 4.1 Настройка доступности пользователя

```bash
curl -X POST "http://localhost:8004/api/availability" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "work_start_time": "09:00",
    "work_end_time": "18:00",
    "work_days": 31,
    "lunch_start": "13:00",
    "lunch_end": "14:00",
    "timezone": "UTC+3"
  }'
```

#### 4.2 Создание события в календаре

```bash
curl -X POST "http://localhost:8004/api/events" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "title": "Встреча с клиентом",
    "description": "Обсуждение требований к новому функционалу",
    "event_type": "meeting",
    "start_at": "2024-01-16T10:00:00Z",
    "end_at": "2024-01-16T11:00:00Z",
    "location": "Конференц-зал A",
    "participants": [1, 2]
  }'
```

#### 4.3 Проверка доступности времени

```bash
curl -X POST "http://localhost:8004/api/availability/check" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "start_at": "2024-01-16T14:00:00Z",
    "end_at": "2024-01-16T15:00:00Z"
  }'
```

#### 4.4 Получение календаря на период

```bash
curl -X GET "http://localhost:8004/api/calendar?user_id=1&start_date=2024-01-15&end_date=2024-01-21&include_team_events=true&team_id=1"
```

## 🔄 Интеграция через RabbitMQ

### Проверка событий в RabbitMQ

1. Откройте RabbitMQ Management: http://localhost:15672
2. Войдите с admin/admin
3. Перейдите в раздел "Exchanges"
4. Проверьте, что события публикуются при операциях

### Примеры событий:

- `user.created` - создание пользователя
- `user.status_changed` - изменение статуса
- `team.created` - создание команды
- `org_unit.created` - создание подразделения
- `task.created` - создание задачи
- `task.status_changed` - изменение статуса задачи
- `meeting.scheduled` - планирование встречи

## 📊 Тестирование производительности

### Получение статистики пользователя

```bash
curl -X GET "http://localhost:8003/api/performance/user/1?period_start=2024-01-01&period_end=2024-03-31"
```

### Получение статистики команды

```bash
curl -X GET "http://localhost:8003/api/performance/team/1?period_start=2024-01-01&period_end=2024-03-31"
```

## 🛠️ Полезные команды для отладки

### Просмотр логов всех сервисов

```bash
docker-compose logs -f user-service
docker-compose logs -f team-service
docker-compose logs -f task-service
docker-compose logs -f calendar-service
```

### Проверка базы данных

```bash
# Подключение к базам данных
docker-compose exec postgres psql -U postgres -d user_db
docker-compose exec postgres psql -U postgres -d team_db
docker-compose exec postgres psql -U postgres -d task_db
docker-compose exec postgres psql -U postgres -d calendar_db
```

### Полезные SQL запросы

```sql
-- Пользователи с их статусами
SELECT id, email, name, role, status, team_id
FROM users;

-- Организационная структура
SELECT ou.name, ou.level, om.position, om.user_id
FROM org_units ou
         LEFT JOIN org_members om ON ou.id = om.org_unit_id
WHERE ou.is_active = true;

-- Задачи по статусам
SELECT status, COUNT(*) as count
FROM tasks
GROUP BY status;

-- События календаря
SELECT title, start_at, end_at, event_type
FROM calendar_events;
```

## ✅ Чек-лист полного тестирования

### User Service

- [ ] Регистрация пользователей
- [ ] Логин с проверкой статуса
- [ ] Обновление информации пользователя
- [ ] Изменение статуса пользователя
- [ ] Назначение в команду
- [ ] Удаление пользователя

### Team Service

- [ ] Создание команд
- [ ] Создание иерархической структуры
- [ ] Добавление участников
- [ ] Управление участниками
- [ ] Создание новостей
- [ ] CRUD операции

### Task Service

- [ ] Создание задач с приоритетами
- [ ] Изменение статусов задач
- [ ] Добавление комментариев
- [ ] Оценка задач
- [ ] Создание встреч
- [ ] Статистика производительности

### Calendar Service

- [ ] Настройка доступности
- [ ] Создание событий
- [ ] Проверка доступности
- [ ] Просмотр календаря
- [ ] Интеграция с задачами/встречами

### Интеграция

- [ ] События RabbitMQ
- [ ] Синхронизация данных
- [ ] Валидация между сервисами

## 🐛 Устранение неполадок

### Проблемы с миграциями

```bash
# Пересоздание баз данных
docker-compose down -v
docker-compose up -d postgres
# Подождите запуска PostgreSQL
docker-compose up -d
```

### Проблемы с RabbitMQ

```bash
# Проверка подключения
docker-compose exec user-service python -c "
import asyncio
from src.services.rabbitmq import publish_event
asyncio.run(publish_event('test', {'message': 'test'}))
"
```

### Проблемы с портами

```bash
# Проверка занятых портов
netstat -tulpn | grep :800
# Остановка процессов на портах
sudo lsof -ti:8001 | xargs kill -9
``` 