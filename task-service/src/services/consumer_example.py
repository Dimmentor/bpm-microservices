import asyncio, aio_pika, json
from src.config import RABBIT_URL


async def main():
    connection = await aio_pika.connect_robust(RABBIT_URL)
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue("task_events", durable=True)
        await queue.bind("amq.direct", routing_key="task.created")

        async with queue.iterator() as qiter:
            async for message in qiter:
                async with message.process():
                    body = json.loads(message.body.decode())
                    print("Received task.created:", body)


if __name__ == "__main__":
    asyncio.run(main())
