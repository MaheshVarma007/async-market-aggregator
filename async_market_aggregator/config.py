DB_PATH = "./market_data.db"

URLS = [
    "http://httpbin.org/delay/1"
] * 50
#URLS = ["http://api.coindesk.com/v1/bpi/currentprice.json"] * 50

QUEUE_MAXSIZE = 20
NUM_CONSUMERS = 3
