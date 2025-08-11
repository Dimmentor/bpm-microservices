## Инструкция по тестированию микросервисов через Swagger UI

* User Service — работает на порте 8001: http://localhost:8001/docs
* Team Service — работает на порте 8002: http://localhost:8002/docs
* Task Service — работает на порте 8003: http://localhost:8003/docs

## 1. User Service (http://localhost:8001/docs)
### 1.1 Регистрация пользователя 
POST /api/users/register)

Пример запроса:

{
  "email": "john@example.com",
  "password": "mysecretpassword",
  "name": "John Doe",
  "invite_code": "invitecode123"  // если используется приглашения, в первом случае нужно убрать
}


### 1.2 Логин пользователя и получение токена
POST /api/users/login


Пример запроса:

{
  "email": "john@example.com",
  "password": "mysecretpassword",
  "name": "John Doe",
  "invite_code": "invitecode123"
}



## 2. Team Service (http://localhost:8002/docs)
### 2.1 Создание команды (POST /api/teams)
Описание: создаёт новую команду.

Пример запроса:


{
  "name": "Команда 1",
  "description": "Описание команды 1"
}

При создании команды вернется ключ, который можно прописать при регистрации нового пользователя. 

### 2.2 Добавление пользователя в команду (POST /api/teams/{team_id}/add_user или аналог)
Описание: добавить пользователя в команду (проверь точный эндпоинт в swagger).

Пример запроса:

{
  "user_id": 1
}
Что проверить:

Статус 200.

Пользователь связан с командой.

### 2.3 Создание организационного подразделения (POST /org_units)
Описание: Создаёт подразделение внутри команды.

Пример тела запроса:

{
  "team_id": 1,
  "name": "Подразделение команды 1",
  "parent_id": 1,
  "description": "Описание подразделения"
}


### 2.4 Добавление участника в подразделение (POST /org_members)
Описание: Добавляет участника (сотрудника) в организационное подразделение.

Пример тела запроса:

{
  "user_id": 1,
  "org_unit_id": 1,
  "position": "Босс",
  "manager_id": 1
}

## 3. Task Service (http://localhost:8003/docs)
### 3.1 Создание задачи (POST /api/tasks)
Описание: создаёт новую задачу, привязанную к команде или пользователю.

Пример запроса:


{
  "title": "Задача 1",
  "description": "Описание задачи 1",
  "creator_id": 1,
  "assignee_id": 1,
  "team_id": 1,
  "due_at": "2026-08-11T03:45:06.201Z"
}


### 3.2 Получение задачи по id 
GET /api/tasks/1)

### 3.3 Добавление комментария к задаче (POST /tasks/1/comments)
Описание: Добавляет комментарий к задаче с id task_id.

Пример тела запроса:

{
  "task_id": 1,
  "author_id": 1,
  "text": "Сделать это нужно ещё вчера"
}


### 3.4 Оценка задачи (POST /tasks/{task_id}/evaluate)
Описание: Добавляет оценку задаче по критериям.

Пример тела запроса:

{
  "task_id": 1,
  "evaluator_id": 1,
  "criteria": {
    "additionalProp1": 3,
    "additionalProp2": 4,
    "additionalProp3": 5
  }
}

Возвращается JSON с id оценки и score (средняя оценка).

### 3.5 Создание встречи (POST /meetings)
Описание: Создаёт встречу с указанием участников.

Важное условие: start_at должен быть строго раньше end_at.

Пример тела запроса:

{
  "title": "Митинг",
  "creator_id": 1,
  "team_id": 1,
  "start_at": "2025-08-12T03:54:52.590Z",
  "end_at": "2025-08-12T04:54:52.590Z",
  "participants": [
    1
  ]
}


