# SnowCare360 — Reconciled Architecture Decision Report

**Date:** 2026-10-06
**Status:** Approved — Pre-Phase-1

---

## 1. Changes from Original Plan

| # | Original Plan | Decision | Final Design |
|---|---|---|---|
| 1 | All versions in primary table | Separate `*_VERSION` history tables | One authoritative row per clinical table; `*_VERSION` tables hold history |
| 2 | Reuse domain `STATUS` for lifecycle | Add `RECORD_STATUS` | New `RECORD_STATUS` column (`DRAFT/FINAL/AMENDED/VOIDED`). Domain `STATUS` unchanged |
| 3 | Rename all roles to `SNOWCARE_*` | Keep existing names; add `PHYSICIAN_ROLE` | No broad rename. New `PHYSICIAN_ROLE` added |
| 4 | Create `MEMBER_CARE_TEAM` table | Extend `USER_MEMBER_ACCESS` | Add `APP_ROLE`, `GRANTED_BY`, `EXPIRES_AT` columns |
| 5 | One user with multiple secondary roles | Isolated persona test users | Create `SC_PHYSICIAN`, `SC_CARE_MGR`, `SC_COMPLIANCE`, `SC_OPS`, `SC_VIEWER` |
| 6 | All phases equal priority | Security/RBAC, versioning, Studio, Timeline first | Phases 1-3 are P0 |
| 7 | Feature-first approach | Authorization-first approach | `/ask`, Studio, Documents, Audit, Search treated as P0 authorization work |
| 8 | RAP protects Cortex Search | Explicit search filters required | Server-generated `MEMBER_ID` filters on every search call |
| 9 | Search sources lack access metadata | Add `MEMBER_ID`, `RECORD_STATUS` to search sources | Clinical note search includes both; policy/drug search uses `ACCESS_SCOPE=GLOBAL` |
| 10 | Unknown users default to Operations | Deny unknown/unmapped users | Return 403 Forbidden; no silent fallback |
| 11 | f-string SQL with `_safe()` escaping | Parameterized SQL | Stored procedures or REST API bindings for all writes |
| 12 | App runs as ACCOUNTADMIN | Least-privilege `SNOWCARE_APP_ROLE` | Dedicated service role with minimal grants |
| 13 | Admin is clinical author | Admin is system administrator | Clinical override requires explicit reason + audit trail |
| 14 | Mixed Encounter/Visit terminology | ENCOUNTER in DB, "Visits" in UI | Database: `ENCOUNTER`. Frontend label: "Visits" |
| 15 | Implied instant refresh | Honest refresh semantics | Timeline/Overview: live queries. Search: 1-hour lag, disclosed in UI |
| 16 | Audit in Streamlit | Keep detailed audit in React | Streamlit: aggregate metrics only. React: per-user audit |
| 17 | Arbitrary job creation from UI | Controlled templates + read-only history | Jobs page: read-only task history view |
| 18 | Implement first | Document before each phase | This report precedes Phase 1 |

---

## 2. Corrected Snowflake Assumptions

| Assumption | Reality |
|---|---|
| Row Access Policies protect Cortex Search | **Wrong.** Search indexes data at creation. RAPs not enforced at query time. Must use explicit `filter` parameter. |
| REST API `/v2/statements` supports bind parameters | **Partially.** Supports `bindings` in payload. Current `sql_client.py` doesn't use them. Will add support. |
| ACCOUNTADMIN acceptable for app runtime | **Wrong.** Violates least-privilege. Use dedicated `SNOWCARE_APP_ROLE`. |
| Streamlit respects caller identity | **Wrong by default.** SiS runs with owner's rights. No per-user audit data in Streamlit. |
| One user with multiple roles sufficient for testing | **Wrong for auth testing.** Each persona needs its own Snowflake user. |

---

## 3. Final Schema Design

### 3.1 Versioning Columns (added to existing clinical tables)

Tables: `ENCOUNTER`, `MEDICATION`, `DIAGNOSIS`, `LAB_RESULT`, `CLINICAL_NOTE`

```
RECORD_STATUS    VARCHAR DEFAULT 'FINAL'
VERSION_NUMBER   INT DEFAULT 1
UPDATED_BY       VARCHAR
UPDATED_AT       TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
```

### 3.2 Version History Tables

One per clinical entity: `ENCOUNTER_VERSION`, `MEDICATION_VERSION`, `DIAGNOSIS_VERSION`, `LAB_RESULT_VERSION`, `CLINICAL_NOTE_VERSION`

Each contains all parent columns plus:

```
VERSION_ID       VARCHAR NOT NULL  (PK)
CHANGE_REASON    VARCHAR
CHANGED_BY       VARCHAR
CHANGED_AT       TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
```

### 3.3 New AUDIT Schema

```
CLINICAL_COPILOT.AUDIT.CLINICAL_AUDIT_LOG
  AUDIT_ID        VARCHAR NOT NULL
  TABLE_NAME      VARCHAR
  RECORD_ID       VARCHAR
  ACTION          VARCHAR  -- CREATE, FINALIZE, AMEND, VOID
  OLD_STATUS      VARCHAR
  NEW_STATUS      VARCHAR
  CHANGED_BY      VARCHAR
  CHANGE_REASON   VARCHAR
  CHANGED_AT      TIMESTAMP_NTZ
  DETAILS         VARIANT
```

---

## 4. Final Role Model

| Role | Type | Capabilities |
|---|---|---|
| `PHYSICIAN_ROLE` | Persona (NEW) | Clinical read + write on assigned members. Finalize, amend records. |
| `CARE_MANAGER_ROLE` | Persona | Clinical read + write, documents, member studio |
| `COMPLIANCE_ANALYST_ROLE` | Persona | Clinical read, claims, policy, audit read |
| `OPERATIONS_ANALYST_ROLE` | Persona | Member read, claims, jobs read |
| `SNOWCARE_ADMIN_ROLE` | System admin | User management, system config. NOT routine clinical author. |
| `SNOWCARE_APP_ROLE` | Service (NEW) | Least-privilege role for backend service operations |

### Role Hierarchy

```
ACCOUNTADMIN
  └── SNOWCARE_ADMIN_ROLE
        ├── PHYSICIAN_ROLE
        ├── CARE_MANAGER_ROLE
        ├── COMPLIANCE_ANALYST_ROLE
        └── OPERATIONS_ANALYST_ROLE

SNOWCARE_APP_ROLE (independent — not in persona hierarchy)
```

### APP_USER Role Mapping

```
ADMIN              → SNOWCARE_ADMIN_ROLE
PHYSICIAN          → PHYSICIAN_ROLE
CARE_MANAGER       → CARE_MANAGER_ROLE
COMPLIANCE_ANALYST → COMPLIANCE_ANALYST_ROLE
OPS_ANALYST        → OPERATIONS_ANALYST_ROLE
(unknown)          → 403 DENIED
```

---

## 5. Search Authorization

| Search Service | Member-Scoped | Filter Strategy |
|---|---|---|
| `CLINICAL_NOTES_SEARCH` | Yes | `MEMBER_ID` + `RECORD_STATUS` as attributes; backend injects filter |
| `DOCUMENT_SEARCH` | Yes | `MEMBER_ID` from joined DOCUMENT table as attribute; backend injects filter |
| `POLICY_DOCS_SEARCH` | No | Global access; `ACCESS_SCOPE=GLOBAL` attribute |
| `DRUG_INTERACTION_SEARCH` | No | Global access; `ACCESS_SCOPE=GLOBAL` attribute |

Backend flow for `/ask`:
1. Resolve calling user from request headers
2. Query `USER_MEMBER_ACCESS` for authorized member IDs
3. If question mentions a specific `member_id`, verify it's in authorized set
4. Inject `filter` parameter on Cortex Agent search tool calls

---

## 6. Streamlit Security Decision

- **Allowed:** Aggregate population metrics, risk distribution, medication analytics
- **Blocked:** Per-user audit data, member-level PII detail, user-specific views
- **Reason:** SiS runs with owner's rights by default. Caller's rights not yet proven safe.
- **Revisit:** When restricted caller's rights is implemented and tested

---

## 7. Remaining Blockers

| Blocker | Mitigation |
|---|---|
| REST API bindings support untested | Test in Phase 1; fallback to stored procedures |
| Test user creation needs USERADMIN | Current connection has ACCOUNTADMIN |
| Cortex Search recreation causes re-index | Schedule in Phase 3; ~1 hour for clinical notes |
| Missing sequences (`SEQ_MEDICATION`, etc.) | Create or switch to UUID generation |
