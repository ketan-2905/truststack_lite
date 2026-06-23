"""Versioned risk policies (config as code)."""

from app.risk.policies.v1 import POLICY as POLICY_V1

# The active policy used by new recomputations.
ACTIVE_POLICY = POLICY_V1

ALL_POLICIES = {POLICY_V1.version: POLICY_V1}


def get_policy(version: str | None = None):
    if version is None:
        return ACTIVE_POLICY
    return ALL_POLICIES.get(version, ACTIVE_POLICY)
