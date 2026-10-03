# Demo Commands & Walkthrough

Commands and workflows for demonstrating SnowCare360.

## Starting the App

```bash
docker compose up -d
```

Verify both containers are running:

```bash
docker compose ps
```

Health check:

```bash
curl http://localhost:8000/health
```

## API Endpoints Reference

### Member Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /members | List/search members (optional `?q=` query param) |
| GET | /members/{id} | Full member detail with 360 summary |

```bash
# Search for a member by name
curl "http://localhost:8000/members?q=Eleanor"

# Get full detail for member M001
curl http://localhost:8000/members/M001
```

### Agent Endpoint

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /ask | Ask the Cortex Agent a clinical question |

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": "M001",
    "question": "What medications is member M001 taking?",
    "history": []
  }'
```

### Document Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /documents/upload | Upload a document to DOCUMENT_STAGE |
| GET | /documents | List all uploaded documents |

```bash
# Upload a PDF for member M001
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@/path/to/lab_report.pdf" \
  -F "member_id=M001" \
  -F "category=clinical"

# List all documents
curl http://localhost:8000/documents
```

### Member Studio Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /studio/members | Create a synthetic member with clinical data |
| POST | /studio/generate | Generate synthetic clinical records |

```bash
curl -X POST http://localhost:8000/studio/members \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Test",
    "last_name": "Patient",
    "age": 72,
    "gender": "Female",
    "plan_type": "HMO",
    "pcp_name": "Dr. Smith",
    "risk_flags": ["Diabetes", "CKD"]
  }'
```

### Admin Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /admin/users | List application users and roles |
| GET | /admin/audit | View AI audit log |
| GET | /admin/jobs | View task/job status |
| POST | /admin/users/switch-role | Change a user's role |

```bash
# View audit log
curl http://localhost:8000/admin/audit

# List users
curl http://localhost:8000/admin/users

# Switch a user's role
curl -X POST http://localhost:8000/admin/users/switch-role \
  -H "Content-Type: application/json" \
  -d '{"user_id": "U001", "new_role": "admin"}'
```

## Sample Agent Questions

These questions exercise different tools in the Cortex Agent pipeline.

### Medication Queries (triggers: Cortex Analyst + Drug Interaction Search)

```
"What medications is member M001 taking?"
"Are there any drug interactions for member M002?"
"List all active prescriptions for Eleanor."
```

### Risk Assessment (triggers: Cortex Analyst + SCORE_POLYPHARMACY_RISK UDF)

```
"What is the polypharmacy risk for member M003?"
"Which members have the highest medication risk?"
"Does member M001 have any flagged drug pairs?"
```

### Clinical Notes (triggers: Clinical Notes Search)

```
"Summarize the latest clinical notes for member M001."
"What did the provider note about M002's last visit?"
```

### Policy Compliance (triggers: Policy Docs Search + CHECK_POLICY_COMPLIANCE UDF)

```
"Is member M001 compliant with HMO preventive care guidelines?"
"What policy gaps exist for member M003?"
```

### Document Search (triggers: Document Search)

```
"What does the uploaded lab report say about M001's kidney function?"
"Find any uploaded documents related to diabetes management."
```

## Document Upload and Indexing Walkthrough

1. Upload a document:
   ```bash
   curl -X POST http://localhost:8000/documents/upload \
     -F "file=@lab_report.pdf" \
     -F "member_id=M001" \
     -F "category=clinical"
   ```

2. The upload inserts a row into DOCUMENT and stores the file on DOCUMENT_STAGE.

3. DOCUMENT_CHANGE_STREAM captures the insert.

4. DOCUMENT_PROCESSING_TASK runs, chunks the document, and writes to DOCUMENT_CHUNK.

5. DOCUMENT_SEARCH Cortex Search service indexes the chunks (within target lag).

6. The document is now searchable via the agent:
   ```bash
   curl -X POST http://localhost:8000/ask \
     -H "Content-Type: application/json" \
     -d '{
       "member_id": "M001",
       "question": "What does the uploaded lab report say?",
       "history": []
     }'
   ```

## Role Switching

Switch a user's role to test access control:

```bash
# Switch user U001 to readonly
curl -X POST http://localhost:8000/admin/users/switch-role \
  -H "Content-Type: application/json" \
  -d '{"user_id": "U001", "new_role": "readonly"}'
```

Available roles: `clinician`, `admin`, `readonly`.

After switching, endpoints restricted to higher roles will return 403.

## Creating Synthetic Members via Member Studio

Member Studio generates synthetic members with realistic clinical data for testing:

```bash
curl -X POST http://localhost:8000/studio/members \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Demo",
    "last_name": "Patient",
    "age": 68,
    "gender": "Male",
    "plan_type": "PPO",
    "pcp_name": "Dr. Johnson",
    "risk_flags": ["Hypertension", "Polypharmacy"]
  }'
```

This creates the member record and generates associated encounters, medications, diagnoses, and lab results. The new member appears in the dashboard after the MEMBER_360_SUMMARY Dynamic Table refreshes (up to 1 hour) or can be queried directly via `/members/{id}`.

## Running Tests

```bash
python -m tests.test_error_handling
python -m tests.test_new_endpoints
```
