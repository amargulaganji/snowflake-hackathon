# Authorization Model

## Overview

SnowCare360 enforces authorization through three defense-in-depth layers. Each layer is independent -- a request must pass all applicable layers to succeed.

## Three-Layer Authorization

```
Request -> [Layer 1: FastAPI] -> [Layer 2: Snowflake RBAC] -> [Layer 3: Row/Masking Policies] -> Data
```

### Layer 1: FastAPI Route-Level Authorization

FastAPI dependency injection enforces authorization before any handler logic executes:

| Dependency | Purpose |
|---|---|
| `require_authenticated_user()` | Rejects unauthenticated requests (401) |
| `require_permission(permission)` | Checks the user has a specific functional role grant (403) |
| `require_role(role)` | Checks the user holds a specific persona role (403) |

These dependencies read the authenticated identity from `Sf-Context-Current-User` and query Snowflake RBAC to determine the user's granted roles.

### Layer 2: Snowflake RBAC (Grants)

SQL queries execute under the caller's Snowflake session (via `executeAsCaller`). Snowflake enforces table-level grants:

- **4 persona roles**: Map to business functions (admin, care manager, compliance, operations)
- **9 functional roles**: Provide granular, least-privilege access to specific tables/operations
- Persona roles are granted functional roles. Users are granted persona roles.

If a user's role lacks SELECT on a table, the query fails at the Snowflake layer regardless of FastAPI checks.

### Layer 3: Row Access and Masking Policies

Even when a user can access a table, policies filter and mask data:

| Policy | Target | Behavior |
|---|---|---|
| `MEMBER_ACCESS_POLICY` | `MEMBER_ID` column (9 tables) | Filters rows to only members mapped to `CURRENT_USER()` via `USER_MEMBER_ACCESS` |
| `PCP_MASK` | `MEMBER.PCP_NAME` column | Returns `'********'` for non-clinical roles |

## HTTP Status Codes

| Code | Condition |
|---|---|
| 401 | No `Sf-Context-Current-User` header (unauthenticated) |
| 403 | User authenticated but lacks required role or permission |

## Demo Role Preview

The frontend provides a "role preview" feature that lets users preview the UI as different roles. This is a **frontend-only UI toggle** -- it does NOT change backend permissions. The backend always authorizes based on the user's actual Snowflake roles.

## Removed: X-User-Role Header

The `X-User-Role` header was used in an earlier demo prototype. It is now **completely ignored** by the backend. All authorization decisions derive from `Sf-Context-Current-User` and the corresponding Snowflake role grants.

## Authorization Decision Flow

```
1. Is Sf-Context-Current-User present?
   NO  -> 401 Unauthorized
   YES -> Continue

2. Does user's Snowflake role satisfy require_permission / require_role?
   NO  -> 403 Forbidden
   YES -> Continue

3. SQL executes under caller's rights
   - Snowflake RBAC enforces table grants
   - Row access policy filters rows by CURRENT_USER()
   - Masking policy hides sensitive columns per role

4. Response returned to client
```
