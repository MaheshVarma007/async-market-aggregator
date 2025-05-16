import aiohttp
import asyncio
import logging
import time
from datetime import datetime
from aiohttp import ClientTimeout
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, before_sleep_log
from aiolimiter import AsyncLimiter
from async_market_aggregator.metrics import metrics

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

limiter = AsyncLimiter(5, 1)

def log_before_retry(retry_state):
    logger.warning(f"Retrying {retry_state.args[1]} (Attempt {retry_state.attempt_number}) due to {retry_state.outcome.exception()}")


def log_before_retry(retry_state):
    url = retry_state.args[1]
    asyncio.create_task(metrics.record_retry(url))
    logger.warning(f"Retrying {url} (Attempt {retry_state.attempt_number}) due to {retry_state.outcome.exception()}")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=1, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)

async def fetch_with_retry(session, url):
    start = time.monotonic()
    async with limiter:
        latency_wait = time.monotonic() - start
        if latency_wait > 0:
            logger.info(f"⏳ Rate limited: waited {latency_wait:.2f}s before fetching {url}")
        start_fetch = time.monotonic()
        async with session.get(url) as response:
            response.raise_for_status()
            content = await response.text()
            duration = time.monotonic() - start_fetch
            await metrics.record_success(duration)
            return {
                "url": url,
                "timestamp": datetime.utcnow().isoformat(),
                "response_time": round(duration, 3),
                "content": content
            }


async def produce_one(url, queue, session):
    try:
        data = await fetch_with_retry(session, url)

        # Backpressure handling
        while queue.full():
            logger.warning(f"🚦 Queue full! Waiting to enqueue {url}")
            await asyncio.sleep(0.5)

        await queue.put(data)
        logger.info(f"Enqueued data for {url} (Queue size: {queue.qsize()})")
    except asyncio.TimeoutError:
        await metrics.record_timeout()
        await metrics.record_failure()
        raise
    except Exception as e:
        logger.error(f"Failed after retries: {url} | {e}")
        await metrics.record_failure()
        raise

async def producer(urls, queue):
    timeout = ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = [produce_one(url, queue, session) for url in urls]
        await asyncio.gather(*tasks)

