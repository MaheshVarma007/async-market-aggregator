from setuptools import setup, find_packages

setup(
    name="async-market-aggregator",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "aiohttp",
        "aiolimiter",
        "aiosqlite",
        "tenacity",
        "fastapi",
        "uvicorn",
        "prometheus_client"
    ],
    entry_points={
        "console_scripts": [
            "market-aggregator=async_market_aggregator.main:cli_entry"
        ]
    },
)
