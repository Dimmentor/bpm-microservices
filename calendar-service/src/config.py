import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_NAME = os.getenv('DB_NAME', 'calendar_db')
DB_HOST = os.getenv('DB_HOST', 'postgres')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', 'postgres')

# JWT configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'secret')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 1440))

# RabbitMQ configuration
RABBIT_URL = os.getenv('RABBIT_URL', 'amqp://admin:admin@rabbitmq:5672/')