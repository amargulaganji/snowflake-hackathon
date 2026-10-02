# Sentinel360 — Architecture

## Overview

Sentinel360 is a clinical copilot for care management teams. It allows users to search members, view their full clinical profile, and ask natural-language questions answered by an AI agent with full evidence chains.

**Snowflake is the sole data store and reasoning layer.** No external databases, no third-party AI APIs.

## 3-Stage Pipeline Architecture

The Cortex Agent orchestrates a structured 3-stage pipeline for every query:

```
User Question
      │
      ▼
┌─────────────────────────────┐
│  Stage 1: RETRIEVAL         │
│  ─ Cortex Analyst           │  → Structured data (SQL over 5 clinical tables)
│  ─ Clinical Notes Search    │  → Unstructured clinical notes
│  ─ Policy Docs Search       │  → Health plan policy documents
│  ─ Drug Interaction Search  │  → Drug interaction guidelines
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Stage 2: RISK ASSESSMENT   │
│  ─ SCORE_POLYPHARMACY_RISK  │  → Risk level, flagged interactions, reasoning
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Stage 3: COMPLIANCE        │
│  ─ CHECK_POLICY_COMPLIANCE  │  → Compliance status, gaps, cited policies
└─────────────┬───────────────┘
              │
              ▼
      Final Response
      (narrative + evidence chain + risk level + contradiction check)
```

Each stage reports which fields and sources it used. The agent always reports which stage(s) contributed to a given answer.

## Data Model

### Structured Tables (Direct SQL)
| Table | Records | Purpose |
|-------|---------|---------|
| MEMBER | 50 | Demographics, risk flags |
| ENCOUNTER | 108 | Clinical visits |
| MEDICATION | 99 | Prescriptions |
| DIAGNOSIS | 108 | ICD-10 diagnoses |
| LAB_RESULT | 97 | Lab values with reference ranges |
| CLAIM | 24 | Insurance claims with denial reasons |
| ATTACHMENT | 18 | Document metadata |

### Unstructured Tables (Cortex Search)
| Table | Records | Search Service |
|-------|---------|---------------|
| CLINICAL_NOTE | 12 | CLINICAL_NOTES_SEARCH |
| POLICY_DOCUMENT | 14 | POLICY_DOCS_SEARCH |
| DRUG_INTERACTION_GUIDELINE | 16 | DRUG_INTERACTION_SEARCH |

### Semantic View
`CLINICAL_SEMANTIC_VIEW` — dimensions, facts, metrics over the 5 structured tables with 8 verified queries.

## API Layer

| Method | Path | Source | Latency |
|--------|------|--------|---------|
| GET | /members?q= | Direct SQL | ~0.5s |
| GET | /members/{id} | Direct SQL (parallel) | ~0.9s |
| GET | /members/top-risk | Direct SQL | ~0.5s |
| POST | /ask | Cortex Agent | 10-30s |
| GET | /health | — | <50ms |

Member search and detail use direct Snowflake SQL REST API calls — no LLM involved. Only `/ask` routes through the Cortex Agent.

## Guardrails

1. **Evidence Grounding** — every claim backed by tool results
2. **Reasoning Trace** — agent reports fields/tables/documents used
3. **Decline When Uncertain** — explicit when data is insufficient
4. **Contradiction Detection** — flags discrepancies between structured and unstructured sources

## Deployment

- **Local**: Docker Compose (backend + frontend containers)
- **Cloud**: Snowpark Container Services (SPCS) with OAuth token auth
- Backend auto-detects SPCS via `SNOWFLAKE_HOST` env var
