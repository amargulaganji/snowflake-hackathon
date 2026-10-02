from __future__ import annotations

from fastapi import Request, HTTPException

ROLE_PERMISSIONS = {
    'care_manager': ['/members', '/ask', '/health', '/documents'],
    'compliance_analyst': ['/members', '/ask', '/health', '/documents', '/admin/audit'],
    'ops_analyst': ['/members', '/ask', '/health', '/admin/jobs', '/members/risk-deltas', '/members/top-risk'],
    'admin': None,  # None means full access
}


def check_role(request: Request):
    role = request.headers.get('X-User-Role', 'admin')
    if role == 'admin':
        return role
    allowed = ROLE_PERMISSIONS.get(role)
    if allowed is None:
        return role
    path = request.url.path
    if not any(path.startswith(p) for p in allowed):
        raise HTTPException(status_code=403, detail=f'Role {role} not authorized for {path}')
    return role
