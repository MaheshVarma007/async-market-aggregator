import aiosqlite
from async_market_aggregator.config import DB_PATH

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    response_time REAL NOT NULL,
    content TEXT
);
"""

INSERT_SQL = """
INSERT INTO market_data (url, timestamp, response_time, content)
VALUES (?, ?, ?, ?);
"""

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_TABLE_SQL)
        await db.commit()

async def write_to_db(data: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(INSERT_SQL, (
            data["url"],
            data["timestamp"],
            data["response_time"],
            data["content"],
        )):
            await db.commit()
