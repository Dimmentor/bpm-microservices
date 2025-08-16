<h2>Микросервисное приложение на FastAPI. Система управления и контроля бизнеса.</h2>

Основной стек: FastAPI(Python), PostgreSQL, RabbitMQ.

- **User Service** (порт 8001) - управление пользователями, статусами доступа, привязка к командам
- **Team Service** (порт 8002) - управление командами, организационной структурой, новостями
- **Task Service** (порт 8003) - управление задачами, комментариями, оценками, встречами, производительностью
- **Calendar Service** (порт 8004) - управление календарем, проверка доступности времени

### Запуск сервисов
```bash
docker-compose up -build
```
* При этом миграции применятся автоматически, сперва сервисы дождутся запуска RabbitMQ и PostgreSQL.

# Подробный гайд по тестированию эндпоинтов, сгенерировал запросы на ИИ:

## 👤 User Service (8001)

### 1. Регистрация без invite кода

**Запрос:**
```bash
curl -X POST "http://localhost:8001/api/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!",
    "name": "John Doe",
    "phone": "+1234567890",
    "position": "Developer",
    "department": "Engineering"
  }'
```

### 2. Авторизация

**Запрос:**
```bash
curl -X POST "http://localhost:8001/api/users/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'
```

### 3. Получение профиля

**Запрос:**
```bash
curl -X GET "http://localhost:8001/api/users/me" \
  -H "Authorization: Bearer <token>"
```

### 4. Обновление статуса пользователя

**Запрос:**
```bash
curl -X PUT "http://localhost:8001/api/users/1/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_token>" \
  -d '"active"'
```

---

## 🏢 Team Service (8002)

### 1. Создание команды (автоматически создает invite код)

**Запрос:**
```bash
curl -X POST "http://localhost:8002/api/teams" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_token>" \
  -d '{
    "name": "Backend Development Team",
    "description": "Team responsible for backend services",
    "owner_id": 1
  }'
```

**Ожидаемый ответ:**
```json
{
  "id": 1,
  "name": "Backend Development Team",
  "description": "Team responsible for backend services",
  "owner_id": 1,
  "invite_code": "ABC123XY",
  "is_active": true,
  "created_at": "2024-01-15T10:15:00Z"
}
```

### 2. Регистрация с invite кодом

**Запрос:**
```bash
curl -X POST "http://localhost:8001/api/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jane@example.com", 
    "password": "SecurePass123!",
    "name": "Jane Smith",
    "phone": "+1234567891",
    "position": "Team Manager",
    "department": "Engineering",
    "invite_code": "ABC123XY"
  }'
```

### 3. Создание организационного подразделения

**Запрос:**
```bash
curl -X POST "http://localhost:8002/api/org_units" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_token>" \
  -d '{
    "team_id": 1,
    "name": "IT Department",
    "description": "Information Technology Department",
    "parent_id": null
  }'
```

### 4. Добавление участника в команду

**Запрос:**
```bash
curl -X POST "http://localhost:8002/api/teams/1/members?user_id=2&role=developer" \
  -H "Authorization: Bearer <manager_token>"
```

**Ожидаемый ответ:**
```json
{
  "message": "Member added successfully",
  "member_id": 1,
  "team_id": 1,
  "user_id": 2,
  "role": "developer"
}
```

### 5. Получение участников команды

**Запрос:**
```bash
curl -X GET "http://localhost:8002/api/teams/1/members" \
  -H "Authorization: Bearer <token>"
```

### 6. Удаление участника из команды

**Запрос:**
```bash
curl -X DELETE "http://localhost:8002/api/teams/1/members/2" \
  -H "Authorization: Bearer <manager_token>"
```

### 7. Создание новости команды

**Запрос:**
```bash
curl -X POST "http://localhost:8002/api/news" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <manager_token>" \
  -d '{
    "team_id": 1,
    "author_id": 1,
    "title": "Sprint Planning Meeting",
    "content": "Sprint planning meeting scheduled for tomorrow at 10 AM",
    "is_published": true
  }'
```

---

## 📋 Task Service (8003)

### 1. Создание задачи

**Запрос:**
```bash
curl -X POST "http://localhost:8003/api/tasks" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <manager_token>" \
  -d '{
    "title": "Implement user authentication",
    "description": "Add JWT-based authentication to the API",
    "creator_id": 1,
    "assignee_id": 2,
    "team_id": 1,
    "org_unit_id": 1,
    "priority": 2,
    "due_at": "2025-08-15T06:52:47.721Z",
    "estimated_hours": 10
  }'
```

### 2. Обновление статуса задачи

**Запрос:**
```bash
curl -X PUT "http://localhost:8003/api/tasks/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <assignee_token>" \
  -d '{
    "status": "in_progress",
    "actual_hours": 4
  }'
```

### 3. Добавление комментария

**Запрос:**
```bash
curl -X POST "http://localhost:8003/api/tasks/1/comments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "author_id": 2,
    "content": "Started working on JWT implementation. Setting up dependencies."
  }'
```

### 4. Завершение задачи

**Запрос:**
```bash
curl -X PUT "http://localhost:8003/api/tasks/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <assignee_token>" \
  -d '{
    "status": "completed",
    "actual_hours": 14
  }'
```

### 5. Оценка выполненной задачи

**Запрос:**
```bash
curl -X POST "http://localhost:8003/api/tasks/1/evaluate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <manager_token>" \
  -d '{
    "evaluator_id": 1,
    "criteria": {
      "соблюдение_сроков": 4,
      "полнота_выполнения": 5,
      "качество_работы": 4
    },
    "feedback": "Отличная работа! Задача выполнена качественно и в срок."
  }'
```

### 6. Получение матрицы оценок

**Запрос:**
```bash
curl -X GET "http://localhost:8003/api/evaluation/matrix/2?period=quarter" \
  -H "Authorization: Bearer <token>"
```

**Ожидаемый ответ:**
```json
{
  "user_evaluation_matrix": {
    "user_id": 2,
    "period": {
      "start": "2024-10-01T00:00:00",
      "end": "2024-12-31T23:59:59"
    },
    "evaluations_count": 1,
    "average_scores": {
      "соблюдение_сроков": 4.0,
      "полнота_выполнения": 5.0,
      "качество_работы": 4.0
    },
    "overall_average": 4.33
  },
  "comparison": {
    "team_average": {
      "team_id": 1,
      "average_scores": {
        "соблюдение_сроков": 4.0,
        "полнота_выполнения": 5.0,
        "качество_работы": 4.0
      },
      "overall_average": 4.33
    },
    "org_unit_average": {
      "org_unit_id": 1,
      "average_scores": {
        "соблюдение_сроков": 4.0,
        "полнота_выполнения": 5.0,
        "качество_работы": 4.0
      },
      "overall_average": 4.33
    }
  }
}
```

---

## 📅 Calendar Service (8004)

### 1. Настройка доступности пользователя

**Запрос:**
```bash
curl -X POST "http://localhost:8004/api/availability" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "user_id": 1,
    "is_available": true,
    "work_start_time": "09:00",
    "work_end_time": "18:00",
    "timezone": "UTC+3"
  }'
```

### 2. Создание простого события

**Запрос:**
```bash
curl -X POST "http://localhost:8004/api/events" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "user_id": 1,
    "title": "Code Review Session",
    "description": "Review pull requests",
    "event_type": "TASK",
    "start_at": "2024-01-16T14:00:00Z",
    "end_at": "2024-01-16T15:00:00Z",
    "task_id": 1
  }'
```

### 3. Создание встречи с участниками

**Запрос:**
```bash
curl -X POST "http://localhost:8004/api/events" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <manager_token>" \
  -d '{
    "user_id": 2,
    "title": "Sprint Planning",
    "description": "Planning meeting for next sprint",
    "event_type": "MEETING",
    "start_at": "2024-01-17T10:00:00Z",
    "end_at": "2024-01-17T12:00:00Z",
    "location": "Conference Room A",
    "team_id": 1,
    "participants": [1, 2]
  }'
```

### 4. Проверка доступности участников

**Запрос:**
```bash
curl -X POST "http://localhost:8004/api/availability/check" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "user_id": 1,
    "start_at": "2025-08-15T08:09:23.885Z",
    "end_at": "2025-08-15T09:09:23.885Z"
  }'
```

### 5. Получение календаря пользователя

**Запрос:**
```bash
curl -X GET "http://localhost:8004/api/events?user_id=1&start_date=2024-01-15&end_date=2024-01-20" \
  -H "Authorization: Bearer <token>"
```