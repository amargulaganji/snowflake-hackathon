# Authentication Architecture

## Overview

SnowCare360 uses Snowflake-native authentication via SPCS (Snowpark Container Services) public endpoints. All users must authenticate through Snowflake before accessing the application. The legacy X-User-Role demo header system has been fully removed.

## Authentication Flow

```
User -> SPCS Public Endpoint -> Snowflake Login -> SPCS Injects Headers -> FastAPI Backend
```

1. **SPCS public endpoint** forces Snowflake login for every request. No anonymous access is possible.
2. After authentication, SPCS injects the `Sf-Context-Current-User` header containing the authenticated Snowflake username.
3. The `/auth/me` endpoint reads this server-injected header and returns the user's identity. The identity is never client-controlled.

## Caller's Rights (executeAsCaller)

The SPCS service spec enables `executeAsCaller: true`, which provides two key capabilities:

| Capability | Description |
|---|---|
| `Sf-Context-Current-User` | Authenticated username injected by SPCS |
| `Sf-Context-Current-User-Token` | Short-lived token representing the caller's session |

When `executeAsCaller` is enabled, SQL queries execute under the **caller's Snowflake privileges**, not the service owner's. This enforces Snowflake RBAC, row access policies, and masking policies per-user at the database level.

## Service Credentials

Certain operations require service-level access rather than caller-level access:

| Operation | Credential Source | Path |
|---|---|---|
| Cortex Agent API calls | Service token | `/snowflake/session/token` |
| Audit log writes | Service token | `/snowflake/session/token` |
| SQL queries (user data) | Caller's rights token | `Sf-Context-Current-User-Token` |

The service token is obtained from the SPCS token endpoint and represents the service owner's identity. It is used only for operations that require elevated or service-level access (Cortex Agent, audit logging).

## /auth/me Endpoint

```
GET /auth/me -> { "user": "<Sf-Context-Current-User>", "authenticated": true }
```

- Returns the server-derived identity from the `Sf-Context-Current-User` header
- Never trusts or reads client-supplied identity claims
- Returns 401 if the header is missing (unauthenticated request)

## Local Development Fallback

For local development outside SPCS:

| Variable | Purpose |
|---|---|
| `SNOWFLAKE_LOCAL_USER` | Simulates the authenticated username |
| PAT (Personal Access Token) | Authenticates SQL connections to Snowflake |

This fallback is only active when SPCS headers are absent (i.e., running locally). In production (SPCS), the `Sf-Context-Current-User` header always takes precedence.

## Security Guarantees

- All requests to the public endpoint pass through Snowflake authentication
- The `Sf-Context-Current-User` header is injected by SPCS infrastructure and cannot be forged by clients
- SQL queries run under the caller's privileges, enforcing per-user RBAC at the database layer
- Service credentials are scoped to specific backend operations (Cortex Agent, audit)
- The `X-User-Role` header is completely ignored by the backend
