import os
from dotenv import load_dotenv
load_dotenv()

DB_NAME = os.getenv('DB_NAME', 'team_db')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_USER = os.getenv('DB_USER', 'team_user')
DB_PASS = os.getenv('DB_PASS', 'team_pass')

RABBIT_URL = os.getenv('RABBIT_URL', 'amqp://admin:admin@localhost/')
