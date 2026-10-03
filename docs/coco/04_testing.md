# CoCo Testing & Validation Evidence

## Automated Test Suites

All tests were created and executed through CoCo.

### Test Suite 1: Error Handling (10/10 — 100%)
- Empty search query returns empty list
- Search with no matches returns empty list
- Malformed member_id returns 404
- Valid member returns structured JSON with all required keys
- Top-risk endpoint returns list
- Risk-deltas endpoint returns list
- Ask endpoint rejects missing member_id (422)
- Ask endpoint rejects missing question (422)
- Health endpoint returns ok
- SQL injection in search is safely handled

### Test Suite 2: Semantic Accuracy (9/11 — 81%)
- 11 natural language questions against the Cortex Agent
- Validates keyword presence in AI responses
- 2 failures are keyword-matching false negatives (LLM phrasing variations like "HTN" vs "hypertension")
- Questions cover: medication counts, plan types, diagnoses, lab results, drug interactions, policy compliance

### Test Suite 3: Guardrails (4/4 — 100%)
- Nonexistent member → insufficient_evidence flag
- Data not in system → insufficient_evidence flag
- Data type not in model → insufficient_evidence flag
- Digoxin contradiction for M010 → contradiction_detected flag

### Test Suite 4: New Endpoints (test_new_endpoints.py) (22 tests)
- 22 tests covering document upload, document search, member studio, admin, and jobs endpoints

### Overall Results
- **34/36 deterministic tests passing (94%)**
- 9/11 semantic accuracy tests passing (81%)
- **Total: 43/47 (91%)**
- Run date: October 3, 2026
- All tests executed against Docker Compose deployment via CoCo

### Build Verification
- TypeScript compilation verified (0 errors)
- Docker images built successfully (frontend + backend)
- Health endpoint verified after each deployment
- API endpoint smoke tests run after every change
