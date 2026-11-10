# gunicorn.conf.py - Production WSGI/ASGI Server Configuration (Slide 39)
import multiprocessing

bind = "0.0.0.0:5000"
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 60
graceful_timeout = 30
keepalive = 5
preload_app = False
accesslog = "-"
errorlog = "-"
loglevel = "info"
proc_name = "product-api"
