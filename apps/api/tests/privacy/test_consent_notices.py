"""Consent notice versioning, exclusive activation, and public fetch."""

from __future__ import annotations

from app.enums import RoleName


def _admin(client, make_tenant, make_user, slug):
    tenant = make_tenant(slug=slug)
    make_user(tenant, f"admin@{slug}.test", "pw-123456", roles=(RoleName.tenant_admin,))
    token = client.post(
        "/v1/auth/login", json={"email": f"admin@{slug}.test", "password": "pw-123456"}
    ).json()["access_token"]
    return tenant, {"Authorization": f"Bearer {token}"}


def test_create_activate_and_public_fetch(client, make_tenant, make_user):
    tenant, auth = _admin(client, make_tenant, make_user, "notice-1")

    created = client.post(
        "/v1/consent-notices",
        json={
            "key": "onboarding-default",
            "version": 1,
            "jurisdiction": "IN-DPDP",
            "language": "en",
            "title": "Notice",
            "body": "Body text",
            "purposes": ["identity_verification"],
        },
        headers=auth,
    )
    assert created.status_code == 201, created.text
    notice = created.json()
    assert notice["is_active"] is False
    assert len(notice["content_hash"]) == 64

    # Not active yet → public fetch 404.
    pub = client.get(
        "/v1/public/consent-notices/active",
        params={"tenant_slug": tenant.slug, "jurisdiction": "IN-DPDP", "language": "en"},
    )
    assert pub.status_code == 404

    # Activate, then public fetch returns it (no auth required).
    assert client.post(
        f"/v1/consent-notices/{notice['id']}/activate", headers=auth
    ).status_code == 200
    pub = client.get(
        "/v1/public/consent-notices/active",
        params={"tenant_slug": tenant.slug, "jurisdiction": "IN-DPDP", "language": "en"},
    )
    assert pub.status_code == 200
    assert pub.json()["id"] == notice["id"]


def test_activation_is_exclusive_per_key_language(client, make_tenant, make_user):
    tenant, auth = _admin(client, make_tenant, make_user, "notice-2")

    def make(version):
        return client.post(
            "/v1/consent-notices",
            json={
                "key": "onboarding-default",
                "version": version,
                "jurisdiction": "IN-DPDP",
                "language": "en",
                "title": f"v{version}",
                "body": "Body",
                "purposes": ["identity_verification"],
            },
            headers=auth,
        ).json()

    v1, v2 = make(1), make(2)
    client.post(f"/v1/consent-notices/{v1['id']}/activate", headers=auth)
    client.post(f"/v1/consent-notices/{v2['id']}/activate", headers=auth)

    # Only v2 should be active now.
    active = client.get(
        "/v1/consent-notices", params={"active_only": True}, headers=auth
    ).json()
    active_ids = {n["id"] for n in active}
    assert v2["id"] in active_ids
    assert v1["id"] not in active_ids


def test_notice_creation_requires_admin(client, make_tenant, make_api_key):
    tenant = make_tenant(slug="notice-3")
    _, raw = make_api_key(tenant)
    # API keys hold the `system` role, not tenant_admin → 403.
    resp = client.post(
        "/v1/consent-notices",
        json={
            "key": "k",
            "version": 1,
            "jurisdiction": "IN-DPDP",
            "language": "en",
            "title": "t",
            "body": "b",
            "purposes": ["x"],
        },
        headers={"X-API-Key": raw},
    )
    assert resp.status_code == 403
