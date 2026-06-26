"""JWT auth: login, refresh, logout, RBAC, and rate limiting."""

from __future__ import annotations

from app.enums import RoleName


def _login(client, email, password, slug=None):
    body = {"email": email, "password": password}
    if slug:
        body["tenant_slug"] = slug
    return client.post("/v1/auth/login", json=body)


def test_login_success_returns_tokens(client, make_tenant, make_user):
    tenant = make_tenant(slug="login-ok")
    make_user(tenant, "admin@login-ok.test", "s3cret-pw", roles=(RoleName.tenant_admin,))

    resp = _login(client, "admin@login-ok.test", "s3cret-pw")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["access_token"] and body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_login_wrong_password_fails_and_is_audited(client, make_tenant, make_user, db_session):
    tenant = make_tenant(slug="login-bad")
    make_user(tenant, "admin@login-bad.test", "right-pw")

    resp = _login(client, "admin@login-bad.test", "wrong-pw")
    assert resp.status_code == 401

    from sqlalchemy import text

    count = db_session.execute(
        text("SELECT count(*) FROM audit_events WHERE action = 'auth.login_failed'")
    ).scalar()
    assert count == 1


def test_access_token_authorizes_protected_endpoint(client, make_tenant, make_user):
    tenant = make_tenant(slug="rbac-admin")
    make_user(tenant, "admin@rbac.test", "pw-123456", roles=(RoleName.tenant_admin,))
    token = _login(client, "admin@rbac.test", "pw-123456").json()["access_token"]

    # tenant_admin may create an API key.
    resp = client.post(
        "/v1/api-keys", json={"name": "k1"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["raw_key"].startswith("tsk_")


def test_viewer_role_is_forbidden_from_admin_action(client, make_tenant, make_user):
    tenant = make_tenant(slug="rbac-viewer")
    make_user(tenant, "viewer@rbac.test", "pw-123456", roles=(RoleName.viewer,))
    token = _login(client, "viewer@rbac.test", "pw-123456").json()["access_token"]

    resp = client.post(
        "/v1/api-keys", json={"name": "nope"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403


def test_refresh_and_logout_revocation(client, make_tenant, make_user):
    tenant = make_tenant(slug="refresh-flow")
    make_user(tenant, "admin@refresh.test", "pw-123456", roles=(RoleName.tenant_admin,))
    tokens = _login(client, "admin@refresh.test", "pw-123456").json()
    refresh = tokens["refresh_token"]

    # Refresh yields a new access token.
    resp = client.post("/v1/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    assert resp.json()["access_token"]

    # Logout revokes the refresh token.
    resp = client.post("/v1/auth/logout", json={"refresh_token": refresh})
    assert resp.status_code == 204

    resp = client.post("/v1/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 401


def test_login_is_rate_limited(client, make_tenant, make_user, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "rate_limit_auth_per_minute", 3)
    tenant = make_tenant(slug="rl")
    make_user(tenant, "admin@rl.test", "right-pw")

    statuses = [_login(client, "admin@rl.test", "wrong-pw").status_code for _ in range(5)]
    assert statuses.count(429) >= 1, statuses
    # The first few are 401 (auth failures), later ones are 429 (throttled).
    assert statuses[0] == 401
