"""Gunicorn production config for FastAPI with Uvicorn workers"""
import os

port = os.environ.get("PORT", "8000")
bind = f"0.0.0.0:{port}"

# IMPORTANT: Default to 1 worker because conversation state is stored in-memory
# per worker. Multiple workers = different state dicts = context loss between requests.
# Single async UvicornWorker handles concurrent requests fine for small teams.
workers = int(os.environ.get("WEB_CONCURRENCY", 1))

worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = "info"
