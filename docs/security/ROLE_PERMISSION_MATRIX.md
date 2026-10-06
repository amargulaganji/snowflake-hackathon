# Role Permission Matrix

## API Endpoint Access

| Endpoint | Method | CARE_MANAGER | COMPLIANCE_ANALYST | OPERATIONS_ANALYST | SNOWCARE_ADMIN |
|---|---|---|---|---|---|
| `/auth/me` | GET | ALLOW | ALLOW | ALLOW | ALLOW |
| `/members` | GET | ALLOW | ALLOW | ALLOW | ALLOW |
| `/members/{id}` | GET | ALLOW | ALLOW | ALLOW | ALLOW |
| `/ask` | POST | ALLOW | ALLOW | ALLOW | ALLOW |
| `/documents` | GET | ALLOW | DENY | DENY | ALLOW |
| `/documents/upload` | POST | ALLOW | DENY | DENY | ALLOW |
| `/documents/{id}` | DELETE | ALLOW | DENY | DENY | ALLOW |
| `/studio/*` | ALL | ALLOW | ALLOW | ALLOW | ALLOW |
| `/admin/users` | GET | DENY | DENY | DENY | ALLOW |
| `/admin/audit` | GET | DENY | ALLOW | DENY | ALLOW |
| `/admin/jobs` | GET | DENY | DENY | ALLOW | ALLOW |

Notes:
- `/auth/me` requires authentication only (no role check)
- `/members` and `/members/{id}` require `SNOWCARE_MEMBER_READ`; row access policy further filters results
- `/ask` requires authentication; Cortex Agent uses service credentials
- `/studio/*` endpoints require authentication; data access governed by caller's rights

## Data Access (Table-Level Grants)

| Table | CARE_MANAGER | COMPLIANCE_ANALYST | OPERATIONS_ANALYST | SNOWCARE_ADMIN |
|---|---|---|---|---|
| MEMBER | SELECT, INSERT, UPDATE | SELECT | SELECT | ALL |
| MEMBER_MONTH | SELECT | SELECT | SELECT | ALL |
| CLINICAL_CONDITION | SELECT | DENY | DENY | ALL |
| CARE_GAP | SELECT | DENY | DENY | ALL |
| CLAIM | SELECT | SELECT | SELECT | ALL |
| CLAIM_LINE | SELECT | SELECT | SELECT | ALL |
| DOCUMENT | SELECT, INSERT | DENY | DENY | ALL |
| DOCUMENT_CHUNK | SELECT, INSERT | DENY | DENY | ALL |
| POLICY_DOCUMENT | DENY | SELECT | DENY | ALL |
| AUDIT_LOG | DENY | SELECT | DENY | ALL |
| JOB_HISTORY | DENY | DENY | SELECT | ALL |
| USER_MEMBER_ACCESS | SELECT | SELECT | SELECT | ALL |

Notes:
- Row access policy applies to all roles except SNOWCARE_ADMIN
- Masking policy on MEMBER.PCP_NAME: visible to CARE_MANAGER and SNOWCARE_ADMIN only

## Snowflake Resource Access

| Resource | Type | CARE_MANAGER | COMPLIANCE_ANALYST | OPERATIONS_ANALYST | SNOWCARE_ADMIN |
|---|---|---|---|---|---|
| Cortex Agent | Service | Via service creds | Via service creds | Via service creds | Via service creds |
| Cortex Search | Service | Via service creds | Via service creds | Via service creds | Via service creds |
| SNOWCARE360_WH | Warehouse | USAGE | USAGE | USAGE | USAGE, OPERATE |
| SNOWCARE360_DB | Database | USAGE | USAGE | USAGE | ALL |
| SNOWCARE360_SCHEMA | Schema | USAGE | USAGE | USAGE | ALL |
| Stage (documents) | Stage | READ, WRITE | DENY | DENY | ALL |
| UDFs / Procedures | Functions | USAGE | USAGE | USAGE | ALL |

Notes:
- Cortex Agent and Cortex Search operate under **service credentials**, not caller's rights. Row access policies do not filter Cortex Search results.
- Warehouse USAGE is required for all roles to execute queries.
