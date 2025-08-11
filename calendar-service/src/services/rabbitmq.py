import aio_pika
import json
from src.config import RABBIT_URL

async def publish_event(routing_key: str, body: dict):
    connection = await aio_pika.connect_robust(RABBIT_URL)
    async with connection:
        channel = await connection.channel()
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(body).encode()),
            routing_key=routing_key
        )

async def consume_events(queue_name: str, callback):
    connection = await aio_pika.connect_robust(RABBIT_URL)
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(queue_name, durable=True)
        
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    data = json.loads(message.body.decode())
                    await callback(data) 