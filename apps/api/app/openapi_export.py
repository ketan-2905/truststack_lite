"""Dump the generated OpenAPI schema to stdout.

Usage (writes the committed schema on the host):
    docker compose exec -T api python -m app.openapi_export > packages/openapi/openapi.json
"""

from __future__ import annotations

import json
import sys

from app.main import app


def main() -> None:
    json.dump(app.openapi(), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
