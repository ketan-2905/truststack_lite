"""Applicant/case API tests, including audit-trail side effects.

Endpoints are now authenticated (MD 03): B2B tenant clients use an API key.
"""

from __future__ import annotations


def _key_headers(raw_key: str) -> dict:
    return {"X-API-Key": raw_key}


def test_create_applicant_and_case_with_audit(client, make_tenant, make_api_key):
    tenant = make_tenant(name="Acme", slug="acme-test")
    _, raw = make_api_key(tenant)
    headers = _key_headers(raw)

    resp = client.post(
        "/v1/applicants",
        json={"full_name": "Asha Verma", "email": "asha@example.com", "external_ref": "x1"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    applicant = resp.json()
    assert applicant["tenant_id"] == str(tenant.id)
    applicant_id = applicant["id"]

    resp = client.post(
        "/v1/onboarding-cases",
        json={"applicant_id": applicant_id, "reference": "CASE-1"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    case = resp.json()
    assert case["state"] == "created"
    case_id = case["id"]

    resp = client.get(f"/v1/onboarding-cases/{case_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == case_id

    resp = client.get("/v1/audit-events", headers=headers)
    assert resp.status_code == 200
    actions = {e["action"] for e in resp.json()["items"]}
    assert "applicant.created" in actions
    assert "case.created" in actions


def test_missing_auth_is_rejected(client):
    resp = client.post("/v1/applicants", json={"full_name": "No Auth"})
    assert resp.status_code == 401


def test_invalid_api_key_is_rejected(client):
    resp = client.post(
        "/v1/applicants",
        json={"full_name": "Bad Key"},
        headers={"X-API-Key": "tsk_deadbeef_not-a-real-secret"},
    )
    assert resp.status_code == 401


def test_case_cannot_reference_applicant_from_other_tenant(client, make_tenant, make_api_key):
    tenant_a = make_tenant(name="A", slug="a-test")
    tenant_b = make_tenant(name="B", slug="b-test")
    _, raw_a = make_api_key(tenant_a)
    _, raw_b = make_api_key(tenant_b)

    resp = client.post(
        "/v1/applicants", json={"full_name": "Owned by A"}, headers=_key_headers(raw_a)
    )
    applicant_id = resp.json()["id"]

    resp = client.post(
        "/v1/onboarding-cases",
        json={"applicant_id": applicant_id},
        headers=_key_headers(raw_b),
    )
    assert resp.status_code == 404


def test_audit_events_are_tenant_scoped(client, make_tenant, make_api_key):
    tenant_a = make_tenant(name="A", slug="a2-test")
    tenant_b = make_tenant(name="B", slug="b2-test")
    _, raw_a = make_api_key(tenant_a)
    _, raw_b = make_api_key(tenant_b)

    client.post(
        "/v1/applicants", json={"full_name": "A person"}, headers=_key_headers(raw_a)
    )

    resp = client.get("/v1/audit-events", headers=_key_headers(raw_b))
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
