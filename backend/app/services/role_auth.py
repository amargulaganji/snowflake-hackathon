from __future__ import annotations

import logging
from typing import Optional

from fastapi import Request, HTTPException, Depends

from app.auth import (
    get_authenticated_user,
    get_caller_auth_headers,
    is_spcs_authenticated,
    has_caller_token,
)
from app.services.sql_client import sql_client

logger = logging.getLogger("snowcare360.auth")

ROLE_PERMISSIONS: dict[str, list[str] | None] = {
    "SNOWCARE_ADMIN_ROLE": None,
    "CARE_MANAGER_ROLE": [
        "/members", "/ask", "/health", "/documents", "/studio",
        "/auth",
    ],
    "COMPLIANCE_ANALYST_ROLE": [
        "/members", "/ask", "/health", "/documents",
        "/admin/audit", "/auth",
    ],
    "OPERATIONS_ANALYST_ROLE": [
        "/members", "/ask", "/health",
        "/admin/jobs", "/auth",
    ],
}

_user_role_cache: dict[str, str] = {}


async def _resolve_snowflake_role(username: str) -> str:
    if username in _user_role_cache:
        return _user_role_cache[username]
    try:
        rows = await sql_client.execute(
            f"SELECT ROLE FROM APP_USER WHERE UPPER(USERNAME) = '{username.replace(chr(39), chr(39)*2).upper()}'"
        )
        if rows and rows[0].get("ROLE"):
            role = rows[0]["ROLE"].upper()
            role_map = {
                "ADMIN": "SNOWCARE_ADMIN_ROLE",
                "SNOWCARE_ADMIN_ROLE": "SNOWCARE_ADMIN_ROLE",
                "CARE_MANAGER": "CARE_MANAGER_ROLE",
                "CARE_MANAGER_ROLE": "CARE_MANAGER_ROLE",
                "COMPLIANCE_ANALYST": "COMPLIANCE_ANALYST_ROLE",
                "COMPLIANCE_ANALYST_ROLE": "COMPLIANCE_ANALYST_ROLE",
                "OPS_ANALYST": "OPERATIONS_ANALYST_ROLE",
                "OPERATIONS_ANALYST": "OPERATIONS_ANALYST_ROLE",
                "OPERATIONS_ANALYST_ROLE": "OPERATIONS_ANALYST_ROLE",
            }
            resolved = role_map.get(role, "OPERATIONS_ANALYST_ROLE")
            _user_role_cache[username] = resolved
            return resolved
    except Exception as exc:
        logger.warning("Failed to resolve role for %s: %s", username, exc)
    return "OPERATIONS_ANALYST_ROLE"


class AuthenticatedUser:
    def __init__(self, username: str, role: str, request: Request):
        self.username = username
        self.role = role
        self.request = request
        self._caller_headers: dict[str, str] | None = None

    @property
    def caller_headers(self) -> dict[str, str]:
        if self._caller_headers is None:
            self._caller_headers = get_caller_auth_headers(self.request)
        return self._caller_headers

    @property
    def is_admin(self) -> bool:
        return self.role == "SNOWCARE_ADMIN_ROLE"


async def require_authenticated_user(request: Request) -> AuthenticatedUser:
    username = get_authenticated_user(request)
    if not username:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Access via Snowflake-authenticated SPCS endpoint.",
        )
    role = await _resolve_snowflake_role(username)
    return AuthenticatedUser(username=username, role=role, request=request)


async def require_permission(request: Request) -> AuthenticatedUser:
    user = await require_authenticated_user(request)
    allowed = ROLE_PERMISSIONS.get(user.role)
    if allowed is None:
        return user
    path = request.url.path
    if not any(path.startswith(p) for p in allowed):
        raise HTTPException(
            status_code=403,
            detail=f"Role {user.role} is not authorized for {path}",
        )
    return user


def require_role(*roles: str):
    async def _dependency(request: Request) -> AuthenticatedUser:
        user = await require_authenticated_user(request)
        if user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"Requires one of {roles}, current role: {user.role}",
            )
        return user
    return _dependency


def require_any_role(*roles: str):
    return require_role(*roles)


# Backward-compatible: used by studio.py dependencies
async def check_role(request: Request) -> str:
    user = await require_permission(request)
    return user.role
