"""Deterministic content hashing for consent notices and receipts.

Canonical JSON (sorted keys, no whitespace) ensures the same logical content
always hashes to the same value, which is what makes consent receipts verifiable
and immutable.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def sha256_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def canonical_hash(obj: Any) -> str:
    return sha256_hex(canonical_json(obj))
