1. Клонируйте репозиторий
git clone https://github.com/Dimmentor/bpm-microservices.git
cd bpm-microservices
2. Запустите проект
bash
Копировать
Редактировать
docker-compose up --build

📡 Доступ к сервисам
Сервис	URL Swagger UI	Порт на хосте
User Service	http://localhost:8001/docs	8001
Team Service	http://localhost:8002/docs	8002
Task Service	http://localhost:8003/docs	8003
RabbitMQ UI	http://localhost:15672	15672 (логин/пароль: guest/guest)