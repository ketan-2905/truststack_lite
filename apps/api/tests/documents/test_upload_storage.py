"""Document upload, storage, checksum, and dependency-failure tests.

Run against real MinIO inside the api container. OCR is not configured locally,
so processing fails loudly with 424 (no fake OCR success)."""

from __future__ import annotations

import io

from PIL import Image


def _png_bytes(color: str = "white", size=(200, 100)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def _hdr(raw: str) -> dict:
    return {"X-API-Key": raw}


def _upload(client, case_id, raw, content, *, process: bool, doc_type="pan", name="id.png"):
    return client.post(
        f"/v1/onboarding-cases/{case_id}/documents",
        params={"process": str(process).lower()},
        files={"file": (name, content, "image/png")},
        data={"doc_type": doc_type},
        headers=_hdr(raw),
    )


def test_upload_stores_object_and_checksum(
    client, make_tenant, make_api_key, make_applicant, make_case, db_session
):
    tenant = make_tenant(slug="doc-1")
    _, raw = make_api_key(tenant)
    applicant = make_applicant(tenant)
    case = make_case(tenant, applicant)
    content = _png_bytes()

    resp = _upload(client, case.id, raw, content, process=False)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "uploaded"
    assert len(body["content_sha256"]) == 64

    # The object really exists in MinIO and metadata is persisted.
    from app.models.document import Document
    from app.storage import object_exists

    doc = db_session.get(Document, body["id"])
    assert doc is not None
    assert doc.size_bytes == len(content)
    assert object_exists(doc.storage_key)


def test_processing_without_ocr_returns_424_and_records_failure(
    client, make_tenant, make_api_key, make_applicant, make_case, db_session, monkeypatch
):
    # Force OCR unconfigured so this deterministically tests the dependency path
    # regardless of whether OCR credentials exist in the environment.
    from app.config import settings

    monkeypatch.setattr(settings, "ocr_provider", None)
    tenant = make_tenant(slug="doc-2")
    _, raw = make_api_key(tenant)
    applicant = make_applicant(tenant)
    case = make_case(tenant, applicant)

    resp = _upload(client, case.id, raw, _png_bytes(), process=True)
    assert resp.status_code == 424, resp.text
    assert resp.json()["detail"]["code"] == "dependency_not_configured"

    # Document was still stored, marked failed, with a dependency_not_configured step.
    from sqlalchemy import text

    doc_status = db_session.execute(
        text("SELECT status FROM documents WHERE tenant_id = :t"),
        {"t": str(tenant.id)},
    ).scalar()
    assert doc_status == "failed"
    step_status = db_session.execute(
        text("SELECT status FROM verification_steps WHERE tenant_id = :t AND step_type='document_ocr'"),
        {"t": str(tenant.id)},
    ).scalar()
    assert step_status == "dependency_not_configured"


def test_unsupported_file_type_rejected(
    client, make_tenant, make_api_key, make_applicant, make_case
):
    tenant = make_tenant(slug="doc-3")
    _, raw = make_api_key(tenant)
    applicant = make_applicant(tenant)
    case = make_case(tenant, applicant)

    resp = client.post(
        f"/v1/onboarding-cases/{case.id}/documents",
        params={"process": "false"},
        files={"file": ("x.txt", b"hello", "text/plain")},
        data={"doc_type": "pan"},
        headers=_hdr(raw),
    )
    assert resp.status_code == 409


def test_duplicate_checksum_across_applicants_raises_signal(
    client, make_tenant, make_api_key, make_applicant, make_case, db_session
):
    tenant = make_tenant(slug="doc-4")
    _, raw = make_api_key(tenant)
    content = _png_bytes(color="white", size=(123, 77))  # stable bytes

    applicant_a = make_applicant(tenant, full_name="A")
    case_a = make_case(tenant, applicant_a)
    applicant_b = make_applicant(tenant, full_name="B")
    case_b = make_case(tenant, applicant_b)

    assert _upload(client, case_a.id, raw, content, process=False).status_code == 201
    assert _upload(client, case_b.id, raw, content, process=False).status_code == 201

    from sqlalchemy import text

    count = db_session.execute(
        text("SELECT count(*) FROM risk_signals WHERE tenant_id = :t AND code = 'duplicate_artifact'"),
        {"t": str(tenant.id)},
    ).scalar()
    assert count == 1


def test_preview_requires_redacted_artifact(
    client, make_tenant, make_api_key, make_applicant, make_case
):
    tenant = make_tenant(slug="doc-5")
    _, raw = make_api_key(tenant)
    applicant = make_applicant(tenant)
    case = make_case(tenant, applicant)
    doc_id = _upload(client, case.id, raw, _png_bytes(), process=False).json()["id"]

    # No redacted derivative yet (OCR unconfigured) → preview 404, never raw.
    resp = client.get(f"/v1/documents/{doc_id}/preview", headers=_hdr(raw))
    assert resp.status_code == 404
