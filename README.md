# URL Shortener

A fast, self-hosted URL shortener built with **FastAPI**, **MongoDB**, and **Redis**.

Paste a long URL, get a short link back. Supports custom short codes and optional expiration.

---

## Features

- **Shorten URLs** — generate a random 7-character short code or pick your own custom alias
- **Custom codes** — use human-readable slugs like `my-link` (3–20 chars, alphanumeric + `-` `_`)
- **Link expiration** — set URLs to auto-expire after 1 hour, 1 day, 7 days, or 30 days
- **Redis caching** — redirects are served from cache for speed; falls back to MongoDB if Redis is unavailable
- **MongoDB TTL index** — expired documents are automatically cleaned up by MongoDB
- **Health check endpoint** — verify MongoDB and Redis connectivity at a glance
- **Docker-ready** — one command to spin up the full stack
- **Minimal frontend** — clean HTML/CSS/JS interface, no framework required

---

## Architecture

```
┌────────────┐       POST /urls        ┌─────────────┐
│  Frontend   │ ─────────────────────▶  │   FastAPI    │
│  (Browser)  │ ◀─────────────────────  │   Server    │
└────────────┘       short_url         └──────┬──────┘
                                              │
                    GET /{code}               │
              ┌───────────────────────────────┤
              │                               │
              ▼                               ▼
       ┌────────────┐                 ┌────────────┐
       │    Redis    │  cache miss ──▶ │  MongoDB   │
       │   (cache)   │ ◀── backfill ── │  (store)   │
       └────────────┘                 └────────────┘
```

**Redirect flow:**
1. Check Redis cache for the short code
2. On cache miss (or Redis failure), query MongoDB
3. If found in MongoDB, cache the result in Redis with appropriate TTL
4. Return a `307 Temporary Redirect` to the original URL

---

## Tech Stack

| Layer    | Technology                  |
| -------- | --------------------------- |
| API      | FastAPI + Uvicorn           |
| Database | MongoDB 8 (via Motor async) |
| Cache    | Redis 7                     |
| Frontend | Vanilla HTML / CSS / JS     |
| Deploy   | Docker + Docker Compose     |

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- (Optional) Python 3.12+ if you want to run the backend locally without Docker

### Quick Start (Docker) — Recommended

**1. Clone the repository**

```bash
git clone https://github.com/VMadhav007/URL_shortner.git
cd URL_shortner
```

**2. Create the `.env` file**

```bash
cat > .env << EOF
MONGO_URL=mongodb://mongodb:27017
MONGO_DB=url_db
REDIS_URL=redis://redis:6379
EOF
```

**3. Start everything**

```bash
docker compose up --build -d
```

This spins up three containers:

| Container      | Port | Purpose       |
| -------------- | ---- | ------------- |
| `url_api`      | 8000 | FastAPI server |
| `url_mongodb`  | —    | MongoDB       |
| `url_redis`    | —    | Redis cache   |

**4. Open the frontend**

Open `frontend/index.html` in your browser (or use a local server like VS Code Live Server on port 5500).

> The frontend expects the API at `http://127.0.0.1:8000`. If you change the API port, update the `fetch` URL in `frontend/script.js`.

**5. Start shortening!**

Paste any URL, optionally pick a custom code and expiration, and click **Shorten URL**.

---

### Local Development (Without Docker)

If you prefer running the backend directly on your machine:

**1. Install MongoDB and Redis locally**

- MongoDB: https://www.mongodb.com/docs/manual/installation/
- Redis: https://redis.io/docs/getting-started/installation/

Make sure both services are running.

**2. Create a virtual environment and install dependencies**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**3. Create the `.env` file**

Point to your local MongoDB and Redis instances:

```bash
cat > .env << EOF
MONGO_URL=mongodb://localhost:27017
MONGO_DB=url_db
REDIS_URL=redis://localhost:6379
EOF
```

**4. Start the API server**

```bash
uvicorn app.main:app --reload
```

The API is now running at `http://127.0.0.1:8000`.

**5. Serve the frontend**

Open `frontend/index.html` directly in your browser, or use any local server:

```bash
# Using Python's built-in server
cd frontend
python3 -m http.server 5500
```

Then open `http://localhost:5500` in your browser.

---

## API Reference

### `POST /urls` — Shorten a URL

**Request body** (JSON):

```json
{
  "original_url": "https://example.com/some/very/long/path",
  "custom_code": "my-link",
  "expires_in": 86400
}
```

| Field          | Type     | Required | Description                                                    |
| -------------- | -------- | -------- | -------------------------------------------------------------- |
| `original_url` | `string` | ✅       | The URL to shorten (must be a valid HTTP/HTTPS URL)             |
| `custom_code`  | `string` | ❌       | Custom alias (3–20 chars, `a-z A-Z 0-9 _ -`). Random if omitted |
| `expires_in`   | `int`    | ❌       | Seconds until the link expires. `null` = never expires           |

**Response** `200 OK`:

```json
{
  "short_code": "my-link",
  "short_url": "http://localhost:8000/my-link"
}
```

**Error responses:**

| Status | When                                     |
| ------ | ---------------------------------------- |
| `409`  | Custom code already taken                |
| `422`  | Validation error (bad URL, code too short/long, invalid chars) |
| `500`  | Could not generate unique code after 5 attempts |
| `503`  | Database unavailable                     |

---

### `GET /{short_code}` — Redirect

Redirects to the original URL with a `307 Temporary Redirect`.

Returns `404` if the code doesn't exist or has expired.

---

### `GET /metrics/health` — Health Check

```json
{
  "status": "ok",
  "mongodb": "connected",
  "redis": "connected"
}
```

`status` is `"ok"` when both services are up, or `"degraded"` if either is down.

---

## Usage Examples

### cURL

```bash
# Shorten a URL with a custom code
curl -X POST http://localhost:8000/urls \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://github.com", "custom_code": "gh"}'

# Shorten a URL with auto-generated code + 1-day expiry
curl -X POST http://localhost:8000/urls \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://example.com/long/path", "expires_in": 86400}'

# Use the short link (follows redirect)
curl -L http://localhost:8000/gh

# Health check
curl http://localhost:8000/metrics/health
```

### Python

```python
import requests

response = requests.post("http://localhost:8000/urls", json={
    "original_url": "https://github.com",
    "custom_code": "gh"
})

print(response.json())
# {"short_code": "gh", "short_url": "http://localhost:8000/gh"}
```

### JavaScript (fetch)

```javascript
const response = await fetch("http://localhost:8000/urls", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    original_url: "https://github.com",
    custom_code: "gh",
  }),
});

const data = await response.json();
console.log(data.short_url);
```

---

## Project Structure

```
URL_shortner/
├── app/
│   ├── main.py          # FastAPI app, CORS config, startup indexes
│   ├── routes.py         # API endpoints (create, redirect, health)
│   ├── database.py       # MongoDB (Motor) and Redis connections
│   ├── schemas.py        # Pydantic request/response models
│   ├── models.py         # Data model definitions
│   └── utils.py          # Base62 short code generator
├── frontend/
│   ├── index.html        # Single-page UI
│   ├── style.css         # Styles
│   └── script.js         # Frontend logic (form submission, copy)
├── Dockerfile            # API container image
├── docker-compose.yml    # Full stack orchestration
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (not committed)
└── .gitignore
```

---

## Inspecting the Database

These commands are useful when you want to peek at stored data inside the running containers.

### MongoDB

```bash
# Open a MongoDB shell
docker exec -it url_mongodb mongosh

# Inside mongosh:
use url_db
db.urls.find().pretty()       # View all shortened URLs
db.urls.countDocuments()       # Count total URLs
db.urls.getIndexes()           # Check indexes (short_code unique, expires_at TTL)
db.urls.findOne({ short_code: "gh" })   # Find a specific URL
exit
```

### Redis

```bash
# Open a Redis CLI
docker exec -it url_redis redis-cli

# Inside redis-cli:
KEYS *          # View all cached keys
GET gh          # Get cached original URL for "gh"
TTL gh          # Check remaining cache TTL (seconds)
exit
```

---

## Stopping & Cleanup

```bash
# Stop all containers
docker compose down

# Stop and remove all data (MongoDB + Redis volumes)
docker compose down -v
```

---

## License

This project is open source. Feel free to fork and modify.
