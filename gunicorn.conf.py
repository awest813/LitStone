"""Gunicorn configuration for LitStone production deployments."""
import os

bind = os.environ.get("PORT", "5000")
# Active games live in an in-process dict keyed by game_id, so requests for the
# same session must land in the same worker. Default to a single worker with
# threads; override WEB_CONCURRENCY only if sessions move to a shared backend.
workers = int(os.environ.get("WEB_CONCURRENCY", "1"))
threads = int(os.environ.get("GUNICORN_THREADS", "4"))
timeout = 120
accesslog = "-"
errorlog = "-"
