from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from pymongo.errors import DuplicateKeyError

from app.database import urls_collection, redis_client
from app.schemas import URLCreate, URLResponse
from app.utils import generate_short_code


router = APIRouter()


@router.post("/urls", response_model=URLResponse)
async def create_url(data: URLCreate):

    for _ in range(5):

        short_code = generate_short_code()

        document = {
            "short_code": short_code,
            "original_url": str(data.original_url)
        }

        try:
            await urls_collection.insert_one(document)

            return {
                "short_code": short_code,
                "short_url": f"http://localhost:8000/{short_code}"
            }

        except DuplicateKeyError:
            continue

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

    except Exception:
        # Redis is only a cache.
        # If it fails, continue to MongoDB.
        pass

    # Redis miss or Redis unavailable → MongoDB
    document = await urls_collection.find_one(
        {"short_code": short_code}
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found"
        )

    original_url = document["original_url"]

    # Try to cache the result
    try:
        await redis_client.set(
            short_code,
            original_url,
            ex=3600
        )
    except Exception:
        # Redis failure should not affect the redirect
        pass

    return RedirectResponse(
        url=original_url,
        status_code=307
    )