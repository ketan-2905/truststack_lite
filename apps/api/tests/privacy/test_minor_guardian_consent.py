"""Minor applicants require guardian consent in addition to applicant consent."""

from __future__ import annotations

from datetime import date, timedelta


def _hdr(raw: str) -> dict:
    return {"X-API-Key": raw}


def _minor_dob() -> date:
    # ~10 years old.
    return date.today() - timedelta(days=365 * 10)


def _adult_dob() -> date:
    return date.today() - timedelta(days=365 * 30)


def test_minor_requires_guardian_consent(
    client, make_tenant, make_api_key, make_applicant, make_case, make_consent_notice
):
    tenant = make_tenant(slug="minor-1")
    _, raw = make_api_key(tenant)
    applicant = make_applicant(tenant, full_name="Young One", date_of_birth=_minor_dob())
    case = make_case(tenant, applicant)
    notice = make_consent_notice(tenant)
    headers = _hdr(raw)

    # Applicant consent alone is not enough for a minor.
    client.post(
        f"/v1/onboarding-cases/{case.id}/consents",
        json={"notice_id": str(notice.id), "granted": True, "consent_type": "applicant"},
        headers=headers,
    )
    resp = client.post(f"/v1/onboarding-cases/{case.id}/submit", headers=headers)
    assert resp.status_code == 409
    assert "guardian" in resp.json()["detail"]["message"].lower()

    # Add guardian consent → submit now allowed.
    resp = client.post(
        f"/v1/onboarding-cases/{case.id}/consents",
        json={
            "notice_id": str(notice.id),
            "granted": True,
            "consent_type": "guardian",
            "guardian_name": "Parent Name",
            "guardian_relationship": "mother",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text

    resp = client.post(f"/v1/onboarding-cases/{case.id}/submit", headers=headers)
    assert resp.status_code == 200, resp.text


def test_guardian_consent_requires_guardian_name(
    client, make_tenant, make_api_key, make_applicant, make_case, make_consent_notice
):
    tenant = make_tenant(slug="minor-2")
    _, raw = make_api_key(tenant)
    applicant = make_applicant(tenant, date_of_birth=_minor_dob())
    case = make_case(tenant, applicant)
    notice = make_consent_notice(tenant)

    resp = client.post(
        f"/v1/onboarding-cases/{case.id}/consents",
        json={"notice_id": str(notice.id), "granted": True, "consent_type": "guardian"},
        headers=_hdr(raw),
    )
    assert resp.status_code == 409
    assert "guardian_name" in resp.json()["detail"]["message"]


def test_adult_needs_only_applicant_consent(
    client, make_tenant, make_api_key, make_applicant, make_case, make_consent_notice
):
    tenant = make_tenant(slug="adult-1")
    _, raw = make_api_key(tenant)
    applicant = make_applicant(tenant, date_of_birth=_adult_dob())
    case = make_case(tenant, applicant)
    notice = make_consent_notice(tenant)
    headers = _hdr(raw)

    client.post(
        f"/v1/onboarding-cases/{case.id}/consents",
        json={"notice_id": str(notice.id), "granted": True},
        headers=headers,
    )
    resp = client.post(f"/v1/onboarding-cases/{case.id}/submit", headers=headers)
    assert resp.status_code == 200, resp.text
