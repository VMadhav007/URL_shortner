from fastapi import FastAPI

from app.database import (
    mongo_client,
    redis_client,
    urls_collection
)

from app.routes import router


app = FastAPI()


@app.on_event("startup")
async def startup():
    await urls_collection.create_index(
        "short_code",
        unique=True
    )


app.include_router(router)


@app.get("/health")
async def health():
    await mongo_client.admin.command("ping")
    await redis_client.ping()

    return {
        "status": "ok",
        "mongodb": "connected",
        "redis": "connected"
    }