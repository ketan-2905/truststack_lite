"""Tenant isolation: one tenant's credentials can never read another's data."""

from __future__ import annotations


def _hdr(raw: str) -> dict:
    return {"X-API-Key": raw}


def test_api_key_cannot_read_other_tenant_case(client, make_tenant, make_api_key):
    tenant_a = make_tenant(slug="iso-a")
    tenant_b = make_tenant(slug="iso-b")
    _, raw_a = make_api_key(tenant_a)
    _, raw_b = make_api_key(tenant_b)

    # Tenant A creates an applicant and a case.
    applicant_id = client.post(
        "/v1/applicants", json={"full_name": "A"}, headers=_hdr(raw_a)
    ).json()["id"]
    case_id = client.post(
        "/v1/onboarding-cases", json={"applicant_id": applicant_id}, headers=_hdr(raw_a)
    ).json()["id"]

    # Tenant A can read it.
    assert client.get(f"/v1/onboarding-cases/{case_id}", headers=_hdr(raw_a)).status_code == 200
    # Tenant B cannot — it must look like it does not exist (404, not 403).
    assert client.get(f"/v1/onboarding-cases/{case_id}", headers=_hdr(raw_b)).status_code == 404


def test_api_key_cannot_read_other_tenant_applicant(client, make_tenant, make_api_key):
    tenant_a = make_tenant(slug="iso-a2")
    tenant_b = make_tenant(slug="iso-b2")
    _, raw_a = make_api_key(tenant_a)
    _, raw_b = make_api_key(tenant_b)

    applicant_id = client.post(
        "/v1/applicants", json={"full_name": "A"}, headers=_hdr(raw_a)
    ).json()["id"]

    assert client.get(f"/v1/applicants/{applicant_id}", headers=_hdr(raw_b)).status_code == 404


def test_user_token_is_scoped_to_its_tenant(client, make_tenant, make_user, make_api_key):
    from app.enums import RoleName

    tenant_a = make_tenant(slug="iso-user-a")
    tenant_b = make_tenant(slug="iso-user-b")
    make_user(tenant_a, "admin@iso-a.test", "pw-123456", roles=(RoleName.tenant_admin,))
    _, raw_b = make_api_key(tenant_b)

    # Tenant B creates a case via its API key.
    applicant_id = client.post(
        "/v1/applicants", json={"full_name": "B"}, headers=_hdr(raw_b)
    ).json()["id"]
    case_id = client.post(
        "/v1/onboarding-cases", json={"applicant_id": applicant_id}, headers=_hdr(raw_b)
    ).json()["id"]

    # Tenant A's admin JWT cannot read Tenant B's case.
    token = client.post(
        "/v1/auth/login", json={"email": "admin@iso-a.test", "password": "pw-123456"}
    ).json()["access_token"]
    resp = client.get(
        f"/v1/onboarding-cases/{case_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 404
