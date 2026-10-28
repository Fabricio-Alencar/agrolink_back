import os

import redis
from dotenv import load_dotenv


load_dotenv()


REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", 10000))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")


if not REDIS_HOST:
    raise RuntimeError("REDIS_HOST não foi definida nas variáveis de ambiente")

if not REDIS_PASSWORD:
    raise RuntimeError("REDIS_PASSWORD não foi definida nas variáveis de ambiente")


redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    ssl=True,
    decode_responses=True
)