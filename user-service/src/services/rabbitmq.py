import aio_pika
import json
import asyncio
from src.config import RABBITMQ_URL
import logging

logger = logging.getLogger(__name__)


async def publish_event(routing_key: str, body: dict):
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(body).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=routing_key
            )
    except Exception as e:
        logger.error(f"Failed to publish event: {e}")


async def consume_events(queue_name: str, exchange_name: str, routing_keys: list, callback):
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )

            queue = await channel.declare_queue(
                queue_name,
                durable=True,
                arguments={
                    'x-message-ttl': 86400000,
                    'x-max-length': 10000
                }
            )

            for key in routing_keys:
                await queue.bind(exchange, routing_key=key)

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    try:
                        async with message.process():
                            data = json.loads(message.body.decode())
                            await callback(data)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        await message.nack()
    except Exception as e:
        logger.error(f"Consumer error: {e}")
        await asyncio.sleep(5)
        asyncio.create_task(consume_events(queue_name, exchange_name, routing_keys, callback))
