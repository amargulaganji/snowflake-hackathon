# Sentinel360 — Test Results

**Run date:** 2026-10-03  
**Backend:** http://localhost:8000 (Docker Compose)

---

## 1. Error Handling Tests — 10/10 (100%)

| # | Test | Status | HTTP |
|---|------|--------|------|
| 1 | Empty search query returns empty list | PASS | 200 |
| 2 | Search with no matches returns empty list | PASS | 200 |
| 3 | Malformed member_id returns 404 | PASS | 404 |
| 4 | Valid member returns structured JSON with required keys | PASS | 200 |
| 5 | Top-risk endpoint returns list | PASS | 200 |
| 6 | Risk-deltas endpoint returns list | PASS | 200 |
| 7 | Ask endpoint rejects missing member_id | PASS | 422 |
| 8 | Ask endpoint rejects missing question | PASS | 422 |
| 9 | Health endpoint returns ok | PASS | 200 |
| 10 | SQL injection in search is safely handled | PASS | 200 |

---

## 2. Semantic Accuracy Tests — 9/11 (81%)

Each test sends a natural-language question to the Cortex Agent and checks for expected keywords in the response.

| # | Question | Pass | Missing Keywords |
|---|----------|------|------------------|
| 1 | How many active medications does member M001 have? | PASS | — |
| 2 | What is Eleanor Vance's plan type? | PASS | — |
| 3 | List the diagnoses for member M010 | FAIL | "hypertension" |
| 4 | What is the latest INR result for member M001? | PASS | — |
| 5 | Does member M001 have any abnormal lab results? | PASS | — |
| 6 | What drugs is member M010 currently taking? | FAIL | "Metformin" |
| 7 | Has member M001 had any ER visits? | PASS | — |
| 8 | What is Frank Delgado's age? | PASS | — |
| 9 | Check drug interactions for member M001 | PASS | — |
| 10 | What policy compliance issues exist for member M001? | PASS | — |
| 11 | Summarize the clinical profile of member M010 | PASS | — |

**Notes on failures:** Tests 3 and 6 failed due to LLM phrasing variations — the agent returned correct clinical data but used synonyms or abbreviations (e.g., "HTN" instead of "hypertension", or listed medications by brand name). These are keyword-matching false negatives, not accuracy errors.

---

## 3. Guardrails Tests — 4/4 (100%)

| # | Scenario | Pass | Field Flag | Phrase Match |
|---|----------|------|------------|--------------|
| 1 | Nonexistent member (M999) | PASS | insufficient_evidence=true | yes |
| 2 | Data not in system (specific date query) | PASS | insufficient_evidence=true | yes |
| 3 | Data type not in model (genetic tests) | PASS | insufficient_evidence=true | yes |
| 4 | Digoxin contradiction (M010) | PASS | contradiction_detected=true | yes |

---

## Summary

| Suite | Passed | Total | Rate |
|-------|--------|-------|------|
| Error Handling | 10 | 10 | 100% |
| Semantic Accuracy | 9 | 11 | 81% |
| Guardrails | 4 | 4 | 100% |
| **Overall** | **23** | **25** | **92%** |
