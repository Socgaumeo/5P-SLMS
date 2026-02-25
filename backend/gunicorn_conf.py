"""Gunicorn production config for FastAPI with Uvicorn workers"""
import os

bind = "0.0.0.0:8000"

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
