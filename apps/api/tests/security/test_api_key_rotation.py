"""API key creation, authentication, and rotation semantics."""

from __future__ import annotations

from app.enums import RoleName


def _admin_token(client, make_tenant, make_user, slug):
    tenant = make_tenant(slug=slug)
    make_user(tenant, f"admin@{slug}.test", "pw-123456", roles=(RoleName.tenant_admin,))
    token = client.post(
        "/v1/auth/login", json={"email": f"admin@{slug}.test", "password": "pw-123456"}
    ).json()["access_token"]
    return tenant, {"Authorization": f"Bearer {token}"}


def test_created_key_authenticates_and_is_stored_hashed(
    client, make_tenant, make_user, db_session
):
    _, auth = _admin_token(client, make_tenant, make_user, "rot-1")

    created = client.post("/v1/api-keys", json={"name": "primary"}, headers=auth).json()
    raw = created["raw_key"]
    assert raw.startswith("tsk_")

    # The raw key works for a B2B call.
    resp = client.post("/v1/applicants", json={"full_name": "X"}, headers={"X-API-Key": raw})
    assert resp.status_code == 201

    # Only the hash is stored — the raw key is nowhere in the DB.
    from sqlalchemy import text

    rows = db_session.execute(text("SELECT key_hash FROM tenant_api_keys")).scalars().all()
    assert raw not in rows
    assert all(len(h) == 64 for h in rows)  # sha256 hex


def test_rotation_revokes_old_key_and_issues_new(client, make_tenant, make_user):
    _, auth = _admin_token(client, make_tenant, make_user, "rot-2")

    created = client.post("/v1/api-keys", json={"name": "k"}, headers=auth).json()
    old_raw = created["raw_key"]
    key_id = created["id"]

    # Old key works before rotation.
    assert client.post(
        "/v1/applicants", json={"full_name": "before"}, headers={"X-API-Key": old_raw}
    ).status_code == 201

    rotated = client.post(
        f"/v1/api-keys/{key_id}/rotate", json={"expire_old": True}, headers=auth
    ).json()
    new_raw = rotated["raw_key"]
    assert new_raw != old_raw

    # Old key no longer authenticates; new key does.
    assert client.post(
        "/v1/applicants", json={"full_name": "after-old"}, headers={"X-API-Key": old_raw}
    ).status_code == 401
    assert client.post(
        "/v1/applicants", json={"full_name": "after-new"}, headers={"X-API-Key": new_raw}
    ).status_code == 201


def test_revoked_key_is_rejected(client, make_tenant, make_user):
    _, auth = _admin_token(client, make_tenant, make_user, "rot-3")
    created = client.post("/v1/api-keys", json={"name": "k"}, headers=auth).json()
    raw = created["raw_key"]
    key_id = created["id"]

    assert client.post(f"/v1/api-keys/{key_id}/revoke", headers=auth).status_code == 200
    assert client.post(
        "/v1/applicants", json={"full_name": "x"}, headers={"X-API-Key": raw}
    ).status_code == 401


def test_api_key_creation_is_audited(client, make_tenant, make_user, db_session):
    _, auth = _admin_token(client, make_tenant, make_user, "rot-4")
    client.post("/v1/api-keys", json={"name": "audited"}, headers=auth)

    from sqlalchemy import text

    count = db_session.execute(
        text("SELECT count(*) FROM audit_events WHERE action = 'api_key.created'")
    ).scalar()
    assert count == 1
