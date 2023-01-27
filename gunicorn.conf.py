import os

import uptrace
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor


def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "liquidcore.site.settings")

    if os.getenv('UPTRACE_DSN'):
        uptrace.configure_opentelemetry(
            # Set dsn or use UPTRACE_DSN env var.
            # dsn="",
            service_name="liquidcore",
            service_version="0.0.0",
        )
        DjangoInstrumentor().instrument()
        SQLite3Instrumentor().instrument()
