import asyncio
from collections import defaultdict
from prometheus_client import Counter, Histogram, Gauge

# Prometheus metrics
SUCCESS_COUNT = Counter("fetch_success_total", "Number of successful fetches")
FAILURE_COUNT = Counter("fetch_failure_total", "Number of failed fetches")
TIMEOUT_COUNT = Counter("fetch_timeout_total", "Number of timeouts")
RETRY_COUNT = Counter("fetch_retries_total", "Retry attempts per URL", ["url"])
RESPONSE_TIME = Histogram("fetch_response_seconds", "Response time for successful fetches (seconds)")
QUEUE_SIZE = Gauge("queue_current_size", "Current size of the async queue")

# In-memory tracking for FastAPI /status
class Metrics:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.success_count = 0
        self.failure_count = 0
        self.total_response_time = 0.0
        self.retry_counts = defaultdict(int)
        self.timeout_count = 0

    async def record_success(self, response_time: float):
        async with self.lock:
            self.success_count += 1
            self.total_response_time += response_time
        SUCCESS_COUNT.inc()
        RESPONSE_TIME.observe(response_time)

    async def record_failure(self):
        async with self.lock:
            self.failure_count += 1
        FAILURE_COUNT.inc()

    async def record_retry(self, url: str):
        async with self.lock:
            self.retry_counts[url] += 1
        RETRY_COUNT.labels(url=url).inc()

    async def record_timeout(self):
        async with self.lock:
            self.timeout_count += 1
        TIMEOUT_COUNT.inc()

    async def get_stats(self, queue: asyncio.Queue):
        QUEUE_SIZE.set(queue.qsize())
        async with self.lock:
            avg_response_time = (
                self.total_response_time / self.success_count
                if self.success_count else 0
            )
            return {
                "queue_size": queue.qsize(),
                "success_count": self.success_count,
                "failure_count": self.failure_count,
                "average_response_time": round(avg_response_time, 3),
                "retry_counts": dict(self.retry_counts),
                "timeout_count": self.timeout_count
            }

metrics = Metrics()
