#!/usr/bin/env bash
# Replay failed webhook deliveries via the worker image.
#   bash scripts/replay-webhooks.sh [tenant_id]
set -euo pipefail

COMPOSE="${COMPOSE:-docker compose}"
${COMPOSE} exec -T worker python -m app.cli.replay_webhooks "$@"
