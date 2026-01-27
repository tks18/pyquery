# 🔌 Internal API - The Engine Room

Yo, this is the API. It's built with FastAPI, so it's blazing fast. If you're building a custom frontend or just want to hit the metal, this is for you.

## 🚀 Getting API Access

First off, you need an API key. We don't just let anyone in.
(JK, for now you might need to check the `auth.py` implementation, but assume standard Bearer token vibes).

## 🛣️ Routes

We got a few main routers. All endpoints are prefixed with `/api` (or just `/` depending on how you mount it).

### 🏠 Meta (`/meta`)
Metadata about the service.
*   `GET /`: Health check. "Are you alive?" -> "Yes".

### 📂 Datasets (`/datasets`)
Manage your loaded dataframes.
*   `GET /`: List all datasets currently in memory.
*   `GET /{name}/schema`: Get the schema (columns, types) for a dataset.
*   `GET /{name}/preview`: Get the first N rows (head).

### 📖 Recipes (`/recipes`)
Manage transformation recipes.
*   `POST /apply`: Apply a recipe to a dataset.
*   `GET /history`: See what you've done.

### 📁 Files (`/files`)
File operations.
*   `POST /upload`: Upload a file to the server.
*   `GET /download`: Get a file back.

## 🛡️ Authentication

Most endpoints require an API Key. Pass it in the header:
`X-API-Key: YOUR_SECRET_KEY`

## 🏃‍♀️ Running the Server

```bash
uvicorn pyquery_polars.api.main:app --reload
```
Or just use the CLI:
```bash
pyquery api --port 8000
```
