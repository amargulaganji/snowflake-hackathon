# CoCo Ingenuity Showcase

Evidence of advanced CoCo capabilities used in SnowCare360 beyond the mandatory lifecycle phases.

## 1. Reusable & Shareable Skills (3 skills)

All skills are documented YAML files at the project root, ready to install via `cortex skill install`.

| Skill | File | Purpose | Multi-Agent? |
|-------|------|---------|-------------|
| clinical-safety-review | `clinical-safety-review.skill.yaml` | Comprehensive safety assessment: polypharmacy, drug interactions, abnormal labs, policy compliance | Base skill |
| medication-review | `medication-review.skill.yaml` | Full medication review with 6-step pipeline, hands off to clinical-safety-review if HIGH risk | Orchestrator |
| care-gap-analyzer | `care-gap-analyzer.skill.yaml` | Population-level care gap analysis with fan-out pattern, hands off to medication-review and clinical-safety-review | Coordinator |

### Skill Hierarchy (Multi-Agent Orchestration)

```
care-gap-analyzer (population level)
  |
  +-- medication-review (per-member medication analysis)
  |     |
  |     +-- clinical-safety-review (safety escalation for HIGH risk)
  |
  +-- clinical-safety-review (direct safety escalation)
```

Each skill:
- Has clear input/output contracts
- Documents which Cortex Agent tools it invokes
- Specifies handoff conditions to other skills
- Includes evidence rules (citations, contradiction detection, insufficient evidence)

## 2. MCP Connectors to External Tools

Configuration: `mcp/mcp_config.json`
Skill: `slack-care-alerts.skill.yaml`

### Configured MCP Servers

| Server | Package | Purpose |
|--------|---------|---------|
| SnowCare360-slack | @anthropic-ai/mcp-server-slack | Post care gap alerts, risk summaries, contradiction alerts to Slack channels |
| SnowCare360-gdrive | @anthropic-ai/mcp-server-gdrive | Export compliance reports to shared Google Drive folders |
| SnowCare360-filesystem | @anthropic-ai/mcp-server-filesystem | Save local report exports to ./exports/ |

### Cross-Tool Actions via MCP

The slack-care-alerts skill demonstrates:
- **Slack**: Post formatted care alerts to #care-management, #clinical-ops, #clinical-safety channels
- **Google Drive**: Export PDF compliance reports for audit documentation
- **Filesystem**: Local backup of generated reports

Setup: `cortex mcp add --config mcp/mcp_config.json`

## 3. Automations & Scheduled Runs

### Snowflake-Native Tasks (always running)

| Task | Schedule | Action |
|------|----------|--------|
| RISK_DELTA_NIGHTLY_TASK | Daily 2:00 AM UTC | CALL REFRESH_RISK_DELTAS() -- recomputes risk scores for members with changed medications/labs |
| DOCUMENT_PROCESSING_TASK | Every 5 min (stream-triggered) | Chunks new documents, updates search index status when DOCUMENT_CHANGE_STREAM has data |

### CoCo Automation Candidates

These workflows can be scheduled via `cortex automation create`:

```bash
# Daily care gap analysis at 8am
cortex automation create \
  --schedule "0 8 * * MON-FRI" \
  --prompt "Run care-gap-analyzer for all high-risk members and post results to Slack"

# Weekly medication review for high-risk members
cortex automation create \
  --schedule "0 9 * * MON" \
  --prompt "Run medication-review for each member with 3+ risk flags"

# Daily Slack summary of AI agent activity
cortex automation create \
  --schedule "0 17 * * MON-FRI" \
  --prompt "Query AI_AUDIT_LOG for today's entries, summarize findings, and post to Slack via slack-care-alerts"
```

## 4. Custom Tools & Function Calling

The Cortex Agent has 2 registered custom UDFs that take real actions (not just text):

| Tool | Type | Input | Output |
|------|------|-------|--------|
| SCORE_POLYPHARMACY_RISK | SQL UDF | member_id | VARIANT with risk_level, medication_count, flagged_interactions, reasoning |
| CHECK_POLICY_COMPLIANCE | SQL UDF | member_id, drug_name | VARIANT with compliance_status, applicable_policies, gaps, recommendations |

These are deterministic functions registered as `generic` tools in the agent's YAML spec, callable by the LLM during reasoning.

## 5. Multi-Agent Orchestration

### Pattern: Hierarchical Skill Coordination

Three skills form a coordinated hierarchy:

1. **care-gap-analyzer** (population-level coordinator)
   - Queries all high-risk members
   - Fans out parallel gap checks per member
   - Aggregates findings into population report
   - Hands off critical members to medication-review or clinical-safety-review

2. **medication-review** (member-level orchestrator)
   - Runs 6-step medication analysis pipeline
   - Calls 5 different Cortex Agent tools
   - Conditional handoff to clinical-safety-review when polypharmacy risk is HIGH

3. **clinical-safety-review** (safety specialist)
   - Deep safety assessment with structured output
   - Called directly or via escalation from other skills

### Pattern: CoCo Team Workflow (used in development)

During implementation, CoCo team workflow was used to run parallel agents:
- Agent 1: Frontend component creation
- Agent 2: Backend endpoint implementation
- Agent 3: SQL/Snowflake object creation
- Agent 4: Documentation and testing

## 6. Working Across Surfaces

| Surface | Usage |
|---------|-------|
| **CoCo Desktop** | All planning, development, execution, and testing |
| **Snowflake SPCS** | Production deployment of React+FastAPI app |
| **Streamlit-in-Snowflake** | SnowCare360_DASHBOARD -- population health analytics dashboard accessible directly in Snowsight |
| **Snowsight** | Cortex Agent (CLINICAL_COPILOT_AGENT) is queryable directly in Snowsight via "Ask Cortex" |
| **CoCo Skills** | 3 reusable skills installable in any CoCo session |
| **MCP** | Configured connectors for Slack, Google Drive, filesystem |

The Streamlit dashboard provides a complementary read-only analytics view alongside the interactive SPCS app, demonstrating the same data surfaced through two different Snowflake-native UIs.

## 7. Guardrails & Graceful Fallback

### Agent-Level Guardrails (built into CLINICAL_COPILOT_AGENT instructions)

- **Evidence-grounded only**: Every claim must cite retrieved evidence
- **Decline when uncertain**: "Insufficient evidence to determine [X]"
- **Contradiction detection**: Flags when structured data disagrees with clinical notes
- **Numbered citations**: [1][2][3] format with source attribution

### Application-Level Guardrails

- **Role-based authorization**: Backend middleware blocks unauthorized access (403)
- **Input validation**: Pydantic models reject malformed requests (422)
- **SQL injection prevention**: Parameterized queries, no string interpolation
- **Audit logging**: Every /ask call logged to AI_AUDIT_LOG with tools invoked, latency, guardrail outcomes
- **Error handling**: 10/10 error handling tests pass (empty inputs, malformed IDs, injection attempts)

### Skill-Level Guardrails

All skills include:
- "Never fabricate clinical data"
- "Flag when evidence is insufficient"
- "Note contradictions between structured and unstructured data"
- "Cite sources for every finding"

### Test Coverage

| Test Suite | Guardrail Tests |
|-----------|----------------|
| test_guardrails.py | Nonexistent member, missing data, unknown data type, contradiction detection |
| test_error_handling.py | Empty queries, malformed IDs, SQL injection, missing fields |
| test_new_endpoints.py | Role authorization (403), nonexistent resources (404), empty bodies (422) |
