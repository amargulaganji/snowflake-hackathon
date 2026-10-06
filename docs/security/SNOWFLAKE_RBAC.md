# Snowflake RBAC Configuration

## Reference SQL

All RBAC objects are defined in `sql/11_rbac_and_security.sql`.

## Role Hierarchy

```
ACCOUNTADMIN
  |
  +-- SNOWCARE_ADMIN_ROLE
  |     +-- SNOWCARE_MEMBER_READ
  |     +-- SNOWCARE_MEMBER_WRITE
  |     +-- SNOWCARE_CLINICAL_READ
  |     +-- SNOWCARE_CLAIMS_READ
  |     +-- SNOWCARE_DOCUMENT_READ
  |     +-- SNOWCARE_DOCUMENT_UPLOAD
  |     +-- SNOWCARE_POLICY_READ
  |     +-- SNOWCARE_AUDIT_READ
  |     +-- SNOWCARE_JOB_READ
  |
  +-- CARE_MANAGER_ROLE
  |     +-- SNOWCARE_MEMBER_READ
  |     +-- SNOWCARE_MEMBER_WRITE
  |     +-- SNOWCARE_CLINICAL_READ
  |     +-- SNOWCARE_CLAIMS_READ
  |     +-- SNOWCARE_DOCUMENT_READ
  |     +-- SNOWCARE_DOCUMENT_UPLOAD
  |
  +-- COMPLIANCE_ANALYST_ROLE
  |     +-- SNOWCARE_MEMBER_READ
  |     +-- SNOWCARE_CLAIMS_READ
  |     +-- SNOWCARE_POLICY_READ
  |     +-- SNOWCARE_AUDIT_READ
  |
  +-- OPERATIONS_ANALYST_ROLE
        +-- SNOWCARE_MEMBER_READ
        +-- SNOWCARE_CLAIMS_READ
        +-- SNOWCARE_JOB_READ
```

## Persona Roles

| Role | Description |
|---|---|
| `SNOWCARE_ADMIN_ROLE` | Full access to all data and admin functions |
| `CARE_MANAGER_ROLE` | Clinical care management, member data, documents |
| `COMPLIANCE_ANALYST_ROLE` | Audit, compliance, policy review |
| `OPERATIONS_ANALYST_ROLE` | Operational analytics, claims, job monitoring |

## Functional Roles and Table Grants

| Functional Role | Tables | Grant |
|---|---|---|
| `SNOWCARE_MEMBER_READ` | MEMBER, MEMBER_MONTH, USER_MEMBER_ACCESS | SELECT |
| `SNOWCARE_MEMBER_WRITE` | MEMBER | SELECT, INSERT, UPDATE |
| `SNOWCARE_CLINICAL_READ` | CLINICAL_CONDITION, CARE_GAP | SELECT |
| `SNOWCARE_CLAIMS_READ` | CLAIM, CLAIM_LINE | SELECT |
| `SNOWCARE_DOCUMENT_READ` | DOCUMENT, DOCUMENT_CHUNK | SELECT |
| `SNOWCARE_DOCUMENT_UPLOAD` | DOCUMENT, DOCUMENT_CHUNK | INSERT |
| `SNOWCARE_POLICY_READ` | POLICY_DOCUMENT | SELECT |
| `SNOWCARE_AUDIT_READ` | AUDIT_LOG | SELECT |
| `SNOWCARE_JOB_READ` | JOB_HISTORY | SELECT |

## Caller's Rights (GRANT CALLER)

```sql
GRANT CALLER ON OWNER'S RIGHTS SERVICE snowcare360_service TO ROLE <persona_role>;
```

This allows `executeAsCaller` to function -- SQL statements in the service execute under the calling user's role, not the service owner's.

## Row Access Policy

**MEMBER_ACCESS_POLICY** is applied to the `MEMBER_ID` column on 9 tables:

```sql
CREATE ROW ACCESS POLICY MEMBER_ACCESS_POLICY AS (member_id VARCHAR)
RETURNS BOOLEAN ->
  CURRENT_ROLE() IN ('SNOWCARE_ADMIN_ROLE')
  OR EXISTS (
    SELECT 1 FROM USER_MEMBER_ACCESS
    WHERE USER_NAME = CURRENT_USER() AND MEMBER_ID = member_id
  );
```

- Admins see all rows
- Other users see only rows where `CURRENT_USER()` has a mapping in `USER_MEMBER_ACCESS`

**Applied to**: MEMBER, MEMBER_MONTH, CLINICAL_CONDITION, CARE_GAP, CLAIM, CLAIM_LINE, DOCUMENT, DOCUMENT_CHUNK, AUDIT_LOG

## Masking Policy

**PCP_MASK** is applied to `MEMBER.PCP_NAME`:

```sql
CREATE MASKING POLICY PCP_MASK AS (val VARCHAR) RETURNS VARCHAR ->
  CASE
    WHEN CURRENT_ROLE() IN ('SNOWCARE_ADMIN_ROLE', 'CARE_MANAGER_ROLE')
    THEN val
    ELSE '********'
  END;
```

Only admin and care manager roles see the actual PCP name. All other roles see `'********'`.

## USER_MEMBER_ACCESS Mapping Table

| Column | Type | Description |
|---|---|---|
| `USER_NAME` | VARCHAR | Snowflake username (matches `CURRENT_USER()`) |
| `MEMBER_ID` | VARCHAR | Member ID the user is authorized to access |
| `ASSIGNED_AT` | TIMESTAMP | When access was granted |

This table drives the row access policy. Admins manage it to control which users can see which members.
