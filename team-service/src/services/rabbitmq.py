import aio_pika, json
from src.config import RABBIT_URL


async def publish_event(routing_key: str, body: dict):
    connection = await aio_pika.connect_robust(RABBIT_URL)
    async with connection:
        channel = await connection.channel()
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(body).encode()),
            routing_key=routing_key
        )
