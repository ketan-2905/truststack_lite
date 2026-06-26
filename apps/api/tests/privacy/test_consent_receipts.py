"""Consent receipts: gate, immutability, withdrawal, and timeline."""

from __future__ import annotations


def _hdr(raw: str) -> dict:
    return {"X-API-Key": raw}


def _setup(make_tenant, make_api_key, make_applicant, make_case, make_consent_notice):
    tenant = make_tenant(slug=f"rcpt-{id(make_tenant) % 10000}")
    _, raw = make_api_key(tenant)
    applicant = make_applicant(tenant)
    case = make_case(tenant, applicant)
    notice = make_consent_notice(tenant)
    return tenant, raw, applicant, case, notice


def test_submit_blocked_without_consent_then_allowed(
    client, make_tenant, make_api_key, make_applicant, make_case, make_consent_notice
):
    _, raw, _, case, notice = _setup(
        make_tenant, make_api_key, make_applicant, make_case, make_consent_notice
    )
    headers = _hdr(raw)

    # Before consent → 409 Consent Required.
    resp = client.post(f"/v1/onboarding-cases/{case.id}/submit", headers=headers)
    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "consent_required"

    # Grant consent.
    resp = client.post(
        f"/v1/onboarding-cases/{case.id}/consents",
        json={"notice_id": str(notice.id), "granted": True},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    assert len(resp.json()["receipt_hash"]) == 64

    # Now submit succeeds and advances the case state.
    resp = client.post(f"/v1/onboarding-cases/{case.id}/submit", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["state"] == "documents_pending"


def test_withdrawal_is_a_new_immutable_record_and_reblocks(
    client, make_tenant, make_api_key, make_applicant, make_case, make_consent_notice
):
    _, raw, _, case, notice = _setup(
        make_tenant, make_api_key, make_applicant, make_case, make_consent_notice
    )
    headers = _hdr(raw)

    grant = client.post(
        f"/v1/onboarding-cases/{case.id}/consents",
        json={"notice_id": str(notice.id), "granted": True},
        headers=headers,
    ).json()

    # Withdraw consent — a new record, the old one is untouched.
    withdraw = client.post(
        f"/v1/onboarding-cases/{case.id}/consents/withdraw",
        json={"notice_id": str(notice.id), "reason": "changed mind"},
        headers=headers,
    )
    assert withdraw.status_code == 201
    assert withdraw.json()["granted"] is False
    assert withdraw.json()["id"] != grant["id"]

    # Timeline preserves BOTH records in order (grant then withdrawal).
    timeline = client.get(
        f"/v1/onboarding-cases/{case.id}/consents", headers=headers
    ).json()
    assert [r["granted"] for r in timeline] == [True, False]
    assert timeline[0]["id"] == grant["id"]

    # After withdrawal the gate blocks submission again.
    resp = client.post(f"/v1/onboarding-cases/{case.id}/submit", headers=headers)
    assert resp.status_code == 409


def test_consent_events_are_audited(
    client, make_tenant, make_api_key, make_applicant, make_case, make_consent_notice, db_session
):
    _, raw, _, case, notice = _setup(
        make_tenant, make_api_key, make_applicant, make_case, make_consent_notice
    )
    client.post(
        f"/v1/onboarding-cases/{case.id}/consents",
        json={"notice_id": str(notice.id), "granted": True},
        headers=_hdr(raw),
    )

    from sqlalchemy import text

    count = db_session.execute(
        text("SELECT count(*) FROM audit_events WHERE action = 'consent.granted'")
    ).scalar()
    assert count == 1
