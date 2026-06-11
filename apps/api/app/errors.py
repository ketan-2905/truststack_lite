"""Typed application errors mapped to consistent HTTP responses.

These keep the no-fake-success contract explicit:
``DependencyNotConfiguredError`` -> 424 Failed Dependency
``ConsentRequiredError``         -> 409 Conflict
"""

from __future__ import annotations

from fastapi import HTTPException, status


class AppError(HTTPException):
    """Base for application errors carrying a stable machine-readable code."""

    def __init__(self, status_code: int, code: str, detail: str) -> None:
        super().__init__(status_code=status_code, detail={"code": code, "message": detail})
        self.code = code


class DependencyNotConfiguredError(AppError):
    def __init__(self, dependency: str, required_env: list[str]) -> None:
        super().__init__(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            code="dependency_not_configured",
            detail=(
                f"Required external dependency '{dependency}' is not configured. "
                f"Set the following environment variable(s): {', '.join(required_env)}."
            ),
        )


class ProviderNotConfiguredError(AppError):
    """424 for verification provider config (MD 06 ``missing_provider_config``)."""

    def __init__(self, required_env: list[str]) -> None:
        super().__init__(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            code="missing_provider_config",
            detail=(
                "No verification provider is configured. Set the following "
                f"environment variable(s): {', '.join(required_env)}."
            ),
        )


class ConsentRequiredError(AppError):
    def __init__(self, detail: str = "Required consent is missing for this case.") -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="consent_required",
            detail=detail,
        )


class NotFoundError(AppError):
    def __init__(self, resource: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="not_found",
            detail=f"{resource} not found.",
        )


class ForbiddenError(AppError):
    def __init__(self, detail: str = "You do not have access to this resource.") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="forbidden",
            detail=detail,
        )


class UnauthorizedError(AppError):
    def __init__(self, detail: str = "Authentication required.") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="unauthorized",
            detail=detail,
        )


class ConflictError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="conflict",
            detail=detail,
        )


class RateLimitedError(AppError):
    def __init__(self, detail: str = "Rate limit exceeded. Try again later.") -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="rate_limited",
            detail=detail,
        )
