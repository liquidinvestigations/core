import os

import uptrace
from opentelemetry.instrumentation.django import DjangoInstrumentor
# from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor
# from opentelemetry.instrumentation.logging import LoggingInstrumentor


def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "liquidcore.site.settings")

    if os.getenv('UPTRACE_DSN'):
        if os.getenv('UPTRACE_DSN'):
            uptrace.configure_opentelemetry(
                service_name="liquidcore",
                service_version="0.0.0",
            )
            # LoggingInstrumentor().instrument(set_logging_format=True)
            # SQLite3Instrumentor().instrument()
            DjangoInstrumentor().instrument()
