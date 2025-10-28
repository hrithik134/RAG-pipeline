"""
Gunicorn configuration for production deployment.

This configuration optimizes the RAG Pipeline API for production use with:
- Multiple worker processes for concurrent request handling
- Uvicorn workers for ASGI support (FastAPI compatibility)
- Graceful restarts and timeout handling
- Connection management and keep-alive
"""

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = int(os.getenv("API_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000  # Restart workers after this many requests (prevents memory leaks)
max_requests_jitter = 50  # Add randomness to avoid all workers restarting at once
timeout = 30  # Kill slow requests after 30 seconds
keepalive = 5  # Keep connections alive for 5 seconds

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"  # Log to stderr
loglevel = os.getenv("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "rag-pipeline-api"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed in production)
keyfile = os.getenv("SSL_KEYFILE", None)
certfile = os.getenv("SSL_CERTFILE", None)

# Debugging (should be False in production)
reload = os.getenv("DEBUG", "false").lower() == "true"
reload_engine = "auto"

# Worker lifecycle hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting Gunicorn server")


def on_reload(server):
    """Called when worker is reloaded."""
    server.log.info("Reloading Gunicorn server")


def when_ready(server):
    """Called just after the server is started."""
    server.log.info(f"Server is ready. Spawning {workers} workers")


def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")


def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    worker.log.info(f"Worker initialized (pid: {worker.pid})")


def worker_int(worker):
    """Called when a worker receives the INT or QUIT signal."""
    worker.log.info(f"Worker received INT or QUIT signal (pid: {worker.pid})")


def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info(f"Worker received SIGABRT signal (pid: {worker.pid})")


def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forked child, re-executing.")


def pre_request(worker, req):
    """Called just before a worker processes the request."""
    worker.log.debug(f"{req.method} {req.path}")


def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    pass


def child_exit(server, worker):
    """Called just after a worker has been exited, in the master process."""
    server.log.info(f"Worker exited (pid: {worker.pid})")


def worker_exit(server, worker):
    """Called just after a worker has been exited, in the worker process."""
    pass


def nworkers_changed(server, new_value, old_value):
    """Called just after num_workers has been changed."""
    server.log.info(f"Number of workers changed from {old_value} to {new_value}")


def on_exit(server):
    """Called just before exiting Gunicorn."""
    server.log.info("Shutting down Gunicorn server")

