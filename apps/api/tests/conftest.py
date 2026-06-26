"""Pytest fixtures backed by a REAL, isolated PostgreSQL database.

There is no SQLite/in-memory substitute and no mocked dependency. The session
fixture drops and recreates a dedicated test database, applies the Alembic
migrations against it (proving migrations work from an empty DB), and rebinds
the application's session factory to it. Each test runs against truncated tables
for isolation.
"""

from __future__ import annotations

import os
import uuid

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

import app.db as app_db
from alembic import command
from app.config import settings

TEST_URL = settings.test_database_url


def _reset_test_database() -> None:
    """Drop and recreate the test database via the maintenance connection."""
    url = make_url(TEST_URL)
    db_name = url.database
    maintenance_url = url.set(database="postgres")
    engine = create_engine(maintenance_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(
            text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = :name AND pid <> pg_backend_pid()"
            ),
            {"name": db_name},
        )
        conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))
        conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def _database():
    _reset_test_database()

    # Apply migrations to the fresh test DB (real migration run, not create_all).
    os.environ["ALEMBIC_DATABASE_URL"] = TEST_URL
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    # Rebind the application's engine/session factory to the test database.
    test_engine = create_engine(TEST_URL, pool_pre_ping=True, future=True)
    app_db.engine = test_engine
    app_db.SessionLocal = sessionmaker(
        bind=test_engine, autoflush=False, autocommit=False, future=True
    )
    yield
    test_engine.dispose()


@pytest.fixture(autouse=True)
def _clean_tables():
    """Truncate all domain tables before each test and reseed reference roles."""
    from app.seed import seed_roles

    engine = app_db.engine
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                DO $$
                DECLARE r RECORD;
                BEGIN
                    FOR r IN (
                        SELECT tablename FROM pg_tables
                        WHERE schemaname = 'public' AND tablename <> 'alembic_version'
                    ) LOOP
                        EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' RESTART IDENTITY CASCADE';
                    END LOOP;
                END $$;
                """
            )
        )
    with app_db.SessionLocal() as db:
        seed_roles(db)
        db.commit()

    # Clear Redis state (rate-limit counters, refresh-token allowlist) so tests
    # don't leak throttling/session state into each other.
    from app.redis_client import get_redis

    redis = get_redis()
    for pattern in ("ratelimit:*", "refresh:*"):
        keys = list(redis.scan_iter(pattern))
        if keys:
            redis.delete(*keys)
    yield


@pytest.fixture()
def db_session():
    with app_db.SessionLocal() as session:
        yield session


@pytest.fixture()
def make_tenant(db_session):
    """Factory creating an active tenant directly in the DB."""
    from app.models.tenant import Tenant

    def _make(name: str = "Tenant", slug: str | None = None) -> Tenant:
        tenant = Tenant(
            name=name,
            slug=slug or f"t-{uuid.uuid4().hex[:8]}",
            status="active",
        )
        db_session.add(tenant)
        db_session.commit()
        db_session.refresh(tenant)
        return tenant

    return _make


@pytest.fixture()
def make_user(db_session):
    """Factory creating a user with the given roles in a tenant."""
    from app.enums import RoleName
    from app.models.role import Role, UserRole
    from app.models.user import User
    from app.security import hash_password

    def _make(tenant, email: str, password: str = "pw-12345", roles=(RoleName.tenant_admin,)):
        user = User(
            tenant_id=tenant.id,
            email=email,
            hashed_password=hash_password(password),
            full_name=email.split("@")[0],
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()
        for role_name in roles:
            role = db_session.query(Role).filter(Role.name == role_name).one()
            db_session.add(UserRole(user_id=user.id, role_id=role.id))
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make


@pytest.fixture()
def make_api_key(db_session):
    """Factory creating a tenant API key; returns (ApiKey, raw_key)."""
    from app.services import api_keys as api_key_service

    def _make(tenant, name: str = "test-key"):
        api_key, raw = api_key_service.create_api_key(
            db_session, tenant_id=tenant.id, name=name
        )
        db_session.commit()
        db_session.refresh(api_key)
        return api_key, raw

    return _make


@pytest.fixture()
def make_applicant(db_session):
    """Factory creating an applicant directly in the DB."""
    from datetime import date

    from app.models.applicant import Applicant

    def _make(tenant, full_name: str = "Asha Verma", date_of_birth: date | None = None):
        applicant = Applicant(
            tenant_id=tenant.id,
            full_name=full_name,
            email=None,
            date_of_birth=date_of_birth,
        )
        db_session.add(applicant)
        db_session.commit()
        db_session.refresh(applicant)
        return applicant

    return _make


@pytest.fixture()
def make_case(db_session):
    """Factory creating an onboarding case directly in the DB."""
    from app.enums import CaseState
    from app.models.onboarding_case import OnboardingCase

    def _make(tenant, applicant):
        case = OnboardingCase(
            tenant_id=tenant.id,
            applicant_id=applicant.id,
            state=CaseState.created,
        )
        db_session.add(case)
        db_session.commit()
        db_session.refresh(case)
        return case

    return _make


@pytest.fixture()
def make_consent_notice(db_session):
    """Factory creating (and optionally activating) a consent notice."""
    from app.schemas.consent import ConsentNoticeCreate
    from app.services import consent as consent_service

    def _make(
        tenant,
        *,
        key: str = "onboarding-default",
        version: int = 1,
        jurisdiction: str = "IN-DPDP",
        language: str = "en",
        active: bool = True,
        purposes=("identity_verification",),
    ):
        notice = consent_service.create_notice(
            db_session,
            tenant.id,
            ConsentNoticeCreate(
                key=key,
                version=version,
                jurisdiction=jurisdiction,
                language=language,
                title="Onboarding Consent",
                body="Placeholder consent body pending legal review.",
                purposes=list(purposes),
            ),
        )
        if active:
            consent_service.set_notice_active(db_session, tenant.id, notice.id, True)
        db_session.commit()
        db_session.refresh(notice)
        return notice

    return _make


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c
