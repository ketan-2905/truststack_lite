"""Worker entrypoint: consume RQ queues backed by real Redis.

Runs the full application image so jobs can use the database, object storage,
OCR providers, the risk engine, and webhook delivery. Start with:
    python -m app.worker
"""

from __future__ import annotations

import sys

from rq import Worker

from app.config import settings
from app.logging_config import configure_logging, get_logger
from app.queue import ALL_QUEUES, get_rq_connection

# RQ imports each job's module dynamically by dotted path at execution time, so
# task modules do not need to be imported here.


def main() -> int:
    configure_logging(settings.log_level)
    log = get_logger("truststack.worker")
    connection = get_rq_connection()
    connection.ping()  # fail loudly if Redis is unreachable
    log.info("worker_starting", extra={"fields": {"queues": ALL_QUEUES}})
    worker = Worker(ALL_QUEUES, connection=connection)
    worker.work(with_scheduler=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
