import os
import redis
from dotenv import load_dotenv

load_dotenv()  # loads .env file

r = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True
)

print(r.ping())
