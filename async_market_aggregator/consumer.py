import asyncio
from async_market_aggregator.writer import write_to_db

async def consumer(queue: asyncio.Queue, id: int, stop_event: asyncio.Event):
    while not stop_event.is_set() or not queue.empty():
        try:
            item = await asyncio.wait_for(queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            continue
        if item is None:
            queue.task_done()
            break
        await write_to_db(item)
        print(f"Consumer {id} wrote record from {item['url']}")
        queue.task_done()
