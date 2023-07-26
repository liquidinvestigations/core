import os
from liquidcore import tracing


def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "liquidcore.site.settings")

    tracing.init_tracing('gunicorn')
