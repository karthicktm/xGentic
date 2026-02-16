"""Gunicorn production configuration."""

import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker processes
workers = min(multiprocessing.cpu_count() * 2 + 1, 8)
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120  # Higher for WebSocket connections
keepalive = 5

# Request limits
max_requests = 10000
max_requests_jitter = 1000

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")

# SSL (optional)
certfile = os.getenv("SSL_CERTFILE")
keyfile = os.getenv("SSL_KEYFILE")
