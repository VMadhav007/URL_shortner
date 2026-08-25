from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import (
    mongo_client,
    redis_client,
    urls_collection
)

from app.routes import router


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await urls_collection.create_index(
        "short_code",
        unique=True
    )
    await urls_collection.create_index(
        "expires_at",
        expireAfterSeconds=0
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