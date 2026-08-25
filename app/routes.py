from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from pymongo.errors import DuplicateKeyError, PyMongoError
import redis.exceptions
from datetime import datetime, timedelta, timezone

from app.database import urls_collection, redis_client
from app.schemas import URLCreate, URLResponse
from app.utils import generate_short_code


router = APIRouter()


@router.get("/metrics/health")
async def health_check():

    try:
        await urls_collection.database.command("ping")
        mongodb_status = "connected"
    except PyMongoError:
        mongodb_status = "disconnected"

    try:
        await redis_client.ping()
        redis_status = "connected"
    except redis.exceptions.RedisError:
        redis_status = "disconnected"

    status = "ok" if mongodb_status == "connected" and redis_status == "connected" else "degraded"

    return {
        "status": status,
        "mongodb": mongodb_status,
        "redis": redis_status
    }

@router.post("/urls", response_model=URLResponse)
async def create_url(data: URLCreate):

    # Custom code provided by user
    if data.custom_code:
        short_code = data.custom_code

        now = datetime.now(timezone.utc)
        document = {
            "short_code": short_code,
            "original_url": str(data.original_url),
            "created_at": now
        }
        if data.expires_in:
            document["expires_at"] = now + timedelta(seconds=data.expires_in)

        try:
            await urls_collection.insert_one(document)

        except DuplicateKeyError:
            raise HTTPException(
                status_code=409,
                detail="Custom code already exists"
            )
        except PyMongoError:
            raise HTTPException(
                status_code=503,
                detail="Database error"
            )

        return {
            "short_code": short_code,
            "short_url": f"http://localhost:8000/{short_code}"
        }

    # No custom code → generate random code
    for _ in range(5):

        short_code = generate_short_code()

        now = datetime.now(timezone.utc)
        document = {
            "short_code": short_code,
            "original_url": str(data.original_url),
            "created_at": now
        }
        if data.expires_in:
            document["expires_at"] = now + timedelta(seconds=data.expires_in)

        try:
            await urls_collection.insert_one(document)

            return {
                "short_code": short_code,
                "short_url": f"http://localhost:8000/{short_code}"
            }

        except DuplicateKeyError:
            continue
        except PyMongoError:
            raise HTTPException(
                status_code=503,
                detail="Database error"
            )

    raise HTTPException(
        status_code=500,
        detail="Could not generate a unique short code"
    )


@router.get("/{short_code}")
async def redirect_url(short_code: str):

    # Try Redis first
    try:
        original_url = await redis_client.get(short_code)

        if original_url:
            return RedirectResponse(
                url=original_url,
                status_code=307
            )

    except redis.exceptions.RedisError:
        # Redis is only a cache.
        # If Redis fails, continue to MongoDB.
        pass

    # Redis miss or Redis unavailable → MongoDB
    try:
        document = await urls_collection.find_one(
            {"short_code": short_code}
        )
    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Database error"
        )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found"
        )

    now = datetime.now(timezone.utc)
    if "expires_at" in document and document["expires_at"]:
        expires_at = document["expires_at"]
        # Ensure timezone-aware comparison
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if expires_at < now:
            raise HTTPException(
                status_code=404,
                detail="Short URL not found"
            )
        cache_ttl = int((expires_at - now).total_seconds())
    else:
        cache_ttl = 3600

    original_url = document["original_url"]

    # Try to cache the result
    try:
        if cache_ttl > 0:
            await redis_client.set(
                short_code,
                original_url,
                ex=cache_ttl
            )
    except redis.exceptions.RedisError:
        # Redis failure should not affect the redirect
        pass

    return RedirectResponse(
        url=original_url,
        status_code=307
    )