from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB
mongo_client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
mongo_db = mongo_client[os.getenv("MONGO_DB")]

urls_collection = mongo_db["urls"]


# Redis
redis_client = redis.from_url(
    os.getenv("REDIS_URL"),
    decode_responses=True
)