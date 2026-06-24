"""Replay failed webhook deliveries.

Usage (inside the api/worker container):
    python -m app.cli.replay_webhooks            # replay all failed deliveries
    python -m app.cli.replay_webhooks <tenant_id> # scope to one tenant
"""

from __future__ import annotations

import sys
import uuid

from app.db import SessionLocal
from app.queue import QUEUE_WEBHOOKS, get_queue
from app.services import webhooks as webhook_service

DELIVER_TASK = "app.tasks.webhooks.deliver_webhook"


def replay(tenant_id: uuid.UUID | None = None) -> int:
    with SessionLocal() as db:
        failed = webhook_service.find_failed_deliveries(db, tenant_id)
        queue = get_queue(QUEUE_WEBHOOKS)
        for delivery in failed:
            webhook_service.reset_for_replay(db, delivery)
            queue.enqueue(DELIVER_TASK, str(delivery.id))
        db.commit()
        count = len(failed)
    print(f"Re-enqueued {count} failed webhook deliveries.")
    return count


def main() -> None:
    tenant_id = uuid.UUID(sys.argv[1]) if len(sys.argv) > 1 else None
    replay(tenant_id)


if __name__ == "__main__":
    main()
