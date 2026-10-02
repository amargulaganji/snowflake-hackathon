# Member 360 + Clinical/Regulatory Document Copilot

A healthcare AI copilot powered by Snowflake Cortex Agent that provides member-centric clinical intelligence with evidence-chain reasoning, contradiction detection, and polypharmacy risk scoring.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  React Frontend (Vite + TypeScript)               nginx :80     │
│  Member search sidebar → Chat/query panel → Evidence chain      │
│  Kite theme: #F7F9FB bg, #387ED1 accent, card-based            │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI Backend                                  uvicorn :8000 │
│  GET /members  GET /members/{id}  POST /ask                     │
│  Wraps Cortex Agent REST API — no direct table access           │
├─────────────────────────────────────────────────────────────────┤
│  Snowflake Cortex Agent                                         │
│  Tools: cortex_analyst + cortex_search ×3 + 2 UDFs             │
│  Guardrails: evidence-chain, decline-when-uncertain             │
├─────────────────────────────────────────────────────────────────┤
│  Snowflake Data Layer                                           │
│  Structured: Member, Encounter, Medication, Diagnosis, Lab      │
│  Unstructured: ClinicalNote, PolicyDocument, DrugInteraction    │
│  Semantic View + 3 Cortex Search Services                       │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Docker and Docker Compose
- Snowflake account with Cortex Agent access
- Programmatic Access Token (PAT) for Snowflake authentication

## Setup

### 1. Run SQL setup scripts

Execute the SQL files in `sql/` in order (01 through 08) against your Snowflake account to create the database, tables, synthetic data, semantic view, search services, UDFs, and the Cortex Agent.

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your Snowflake account URL and PAT token.

### 3. Run with Docker Compose

```bash
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Health check: http://localhost:8000/health

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| GET | /members?q={term} | Search members |
| GET | /members/{id} | Get member profile |
| POST | /ask | Ask the clinical copilot |

## Environment Variables

| Variable | Description |
|----------|-------------|
| SNOWFLAKE_ACCOUNT_URL | Snowflake account URL |
| SNOWFLAKE_PAT | Programmatic Access Token |
| SNOWFLAKE_DATABASE | Database name (default: CLINICAL_COPILOT) |
| SNOWFLAKE_SCHEMA | Schema name (default: CORE) |
| SNOWFLAKE_AGENT_NAME | Agent name (default: CLINICAL_COPILOT_AGENT) |
| SNOWFLAKE_WAREHOUSE | Warehouse name (default: COPILOT_WH) |
