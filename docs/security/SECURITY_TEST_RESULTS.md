# Security Test Results

> **Status**: TEMPLATE -- tests not yet executed. Fill in results as testing is performed.

## Environment

| Property | Value |
|---|---|
| Application | SnowCare360 |
| Auth mechanism | Snowflake SPCS public endpoint + `Sf-Context-Current-User` |
| SPCS caller's rights | YES (`executeAsCaller: true` in spec) |
| Snowflake execution identity | Caller's rights for SQL; service credentials for Cortex Agent |
| Snowflake roles created | 13 (4 persona + 9 functional) |
| FastAPI authorization | `require_authenticated_user` / `require_permission` / `require_role` |
| Row access policy | `MEMBER_ACCESS_POLICY` on 9 tables |
| Masking policy | `PCP_MASK` on `MEMBER.PCP_NAME` |

## Test Cases

### Authentication Tests

| # | Test | Expected | Result | Notes |
|---|---|---|---|---|
| A1 | Access public endpoint without Snowflake login | Redirect to Snowflake login | PENDING | |
| A2 | Verify `Sf-Context-Current-User` populated after login | Header contains authenticated username | PENDING | |
| A3 | Call `/auth/me` authenticated | Returns `{ user, authenticated: true }` | PENDING | |
| A4 | Call `/auth/me` unauthenticated | 401 Unauthorized | PENDING | |
| A5 | Forge `Sf-Context-Current-User` via client request | Header ignored; SPCS-injected value used | PENDING | |

### Authorization Tests

| # | Test | Expected | Result | Notes |
|---|---|---|---|---|
| B1 | Care Manager accesses `/members` | 200 OK, filtered by row access policy | PENDING | |
| B2 | Operations Analyst accesses `/documents` | 403 Forbidden | PENDING | |
| B3 | Compliance Analyst accesses `/admin/users` | 403 Forbidden | PENDING | |
| B4 | Admin accesses `/admin/users` | 200 OK | PENDING | |
| B5 | Unauthenticated request to any protected endpoint | 401 Unauthorized | PENDING | |

### X-User-Role Header Tests

| # | Test | Expected | Result | Notes |
|---|---|---|---|---|
| C1 | Send `X-User-Role: ADMIN` as non-admin user | Header ignored; actual role enforced | PENDING | |
| C2 | Send `X-User-Role: CARE_MANAGER` as operations user | Header ignored; actual role enforced | PENDING | |
| C3 | Omit `X-User-Role` entirely | No effect; auth derived from `Sf-Context-Current-User` | PENDING | |

### Row Access Policy Tests

| # | Test | Expected | Result | Notes |
|---|---|---|---|---|
| D1 | Care Manager queries MEMBER table | Only assigned members returned | PENDING | |
| D2 | Admin queries MEMBER table | All members returned | PENDING | |
| D3 | User with no `USER_MEMBER_ACCESS` entries | Zero rows returned | PENDING | |
| D4 | Policy applied across all 9 tables | Consistent filtering per user | PENDING | |

### Masking Policy Tests

| # | Test | Expected | Result | Notes |
|---|---|---|---|---|
| E1 | Care Manager queries `MEMBER.PCP_NAME` | Actual PCP name visible | PENDING | |
| E2 | Operations Analyst queries `MEMBER.PCP_NAME` | Returns `'********'` | PENDING | |
| E3 | Admin queries `MEMBER.PCP_NAME` | Actual PCP name visible | PENDING | |

### Document Authorization Tests

| # | Test | Expected | Result | Notes |
|---|---|---|---|---|
| F1 | Care Manager uploads document | 200 OK | PENDING | |
| F2 | Compliance Analyst reads DOCUMENT table | Access denied (no `SNOWCARE_DOCUMENT_READ`) | PENDING | |
| F3 | Care Manager deletes own document | 200 OK | PENDING | |

### Cortex Agent Tests

| # | Test | Expected | Result | Notes |
|---|---|---|---|---|
| G1 | `/ask` query via Cortex Agent | Agent responds using service credentials | PENDING | |
| G2 | Cortex Search results | Results returned (not filtered by row access policy) | PENDING | |

## Known Limitations

| # | Limitation | Impact | Mitigation |
|---|---|---|---|
| L1 | Cortex Agent uses service credentials, not caller's rights | Agent queries execute as service owner | Row access policies filter caller's direct SQL queries; Cortex responses are supplementary |
| L2 | Cortex Search results not filtered by row access policy | Search may return snippets from members not assigned to the caller | Application-layer filtering planned; current risk accepted for hackathon scope |
| L3 | `INFORMATION_SCHEMA.TASK_HISTORY` requires elevated access | Non-admin users cannot view task history | Job monitoring routed through `JOB_HISTORY` table with appropriate grants |

## Summary

| Category | Total Tests | Passed | Failed | Pending |
|---|---|---|---|---|
| Authentication (A) | 5 | 0 | 0 | 5 |
| Authorization (B) | 5 | 0 | 0 | 5 |
| X-User-Role (C) | 3 | 0 | 0 | 3 |
| Row Access Policy (D) | 4 | 0 | 0 | 4 |
| Masking Policy (E) | 3 | 0 | 0 | 3 |
| Document Auth (F) | 3 | 0 | 0 | 3 |
| Cortex Agent (G) | 2 | 0 | 0 | 2 |
| **Total** | **25** | **0** | **0** | **25** |
