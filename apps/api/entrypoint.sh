#!/bin/sh
if [ -f alembic.ini ]; then
  echo "Applying migrations..."
  alembic upgrade head
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000