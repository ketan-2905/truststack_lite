#!/bin/sh
# API container entrypoint: apply database migrations (when configured) then
# start the API. Migrations are a no-op until MD 02 adds the Alembic config.
set -e

if [ -f alembic.ini ]; then
  echo '{"level":"INFO","logger":"truststack.entrypoint","message":"applying migrations"}'
  alembic upgrade head
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
