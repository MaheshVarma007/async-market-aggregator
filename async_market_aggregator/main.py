import asyncio
import signal
from async_market_aggregator.fetcher import producer
from async_market_aggregator.writer import write_to_db, init_db
from async_market_aggregator.api import app
import uvicorn
import async_market_aggregator.api as api
from contextlib import suppress
import time
from async_market_aggregator.config import URLS, QUEUE_MAXSIZE, NUM_CONSUMERS
from async_market_aggregator.consumer import consumer

# Global task registry
running_tasks = []

async def start_api(queue):
    api.queue_ref = queue
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info", lifespan="off")
    server = uvicorn.Server(config)
    await server.serve()

async def shutdown(signal_name, stop_event, queue):
    print(f"\nReceived {signal_name}. Initiating graceful shutdown...")
    stop_event.set()
    # Wait for queue to drain
    while not queue.empty():
        await asyncio.sleep(0.5)
    # Cancel all running tasks
    for task in running_tasks:
        if not task.done():
            task.cancel()
    print("Shutdown complete.")

async def main():
    await init_db()
    queue = asyncio.Queue(maxsize=QUEUE_MAXSIZE)
    api.queue_ref = queue
    stop_event = asyncio.Event()

    # Register shutdown handler
    loop = asyncio.get_event_loop()
    for sig in [signal.SIGINT, signal.SIGTERM]:
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s.name, stop_event, queue)))

    # Start API
    api_task = asyncio.create_task(start_api(queue))
    running_tasks.append(api_task)

    # Start consumers
    consumer_tasks = [
        asyncio.create_task(consumer(queue, i + 1, stop_event))
        for i in range(NUM_CONSUMERS)
    ]
    running_tasks.extend(consumer_tasks)

    # Start producer
    urls = URLS
    #urls = ["http://api.coindesk.com/v1/bpi/currentprice.json"] * 50

    start_time = time.monotonic()

    producer_task = asyncio.create_task(producer(urls, queue))
    running_tasks.append(producer_task)

    # Wait for producer to finish
    await producer_task

    # After production, wait for queue to drain and signal consumers
    await queue.join()
    stop_event.set()

    for task in consumer_tasks:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    elapsed = time.monotonic() - start_time
    print(f"\nFetched and processed all {len(urls)} requests in {elapsed:.2f} seconds.")

    if elapsed > 5:
        print("Performance test failed: took too long!")
    else:
        print("Performance test passed!")

    await api_task

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Terminated by user")

def cli_entry():
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Terminated by user")
