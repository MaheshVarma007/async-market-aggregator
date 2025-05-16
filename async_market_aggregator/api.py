from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from async_market_aggregator.metrics import metrics
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import asyncio

app = FastAPI()
queue_ref: asyncio.Queue = None  # Will be set from main.py

@app.get("/status")
async def get_status():
    if queue_ref is None:
        return JSONResponse(status_code=503, content={"error": "Queue not initialized"})
    stats = await metrics.get_stats(queue_ref)
    return stats

@app.get("/metrics")
async def prometheus_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
