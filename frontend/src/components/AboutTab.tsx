import { Shield, Eye, MessageSquare, AlertTriangle } from 'lucide-react';

export function AboutTab() {
  return (
    <div className="about-tab">
      <div className="about-header">
        <h2>SnowCare360</h2>
        <p className="about-tagline">Polypharmacy and compliance risk intelligence for care management teams</p>
      </div>

      <div className="about-section about-lead">
        <p>
          SnowCare360 surfaces polypharmacy and compliance risk across your member population,
          grounding every answer in cited clinical and policy evidence. Care managers can identify
          high-risk members, investigate medication interactions, verify policy compliance, and
          generate audit-ready documentation — all from a single interface backed by Snowflake.
        </p>
      </div>

      <div className="about-section">
        <h3>Clinical Guardrails</h3>
        <div className="guardrails-grid">
          <div className="guardrail-card">
            <Eye size={20} />
            <div>
              <strong>Evidence Grounding</strong>
              <p>Every claim is backed by cited data sources — structured records, clinical notes, or policy documents.</p>
            </div>
          </div>
          <div className="guardrail-card">
            <MessageSquare size={20} />
            <div>
              <strong>Reasoning Trace</strong>
              <p>The system reports which tables, fields, and documents contributed to each conclusion.</p>
            </div>
          </div>
          <div className="guardrail-card">
            <Shield size={20} />
            <div>
              <strong>Decline When Uncertain</strong>
              <p>When evidence is insufficient for a complete answer, the system explicitly states what is missing.</p>
            </div>
          </div>
          <div className="guardrail-card">
            <AlertTriangle size={20} />
            <div>
              <strong>Contradiction Detection</strong>
              <p>Flags discrepancies between structured medication records and unstructured clinical notes.</p>
            </div>
          </div>
        </div>
      </div>

      <div className="about-section">
        <h3>Architecture</h3>
        <p>
          Built on Snowflake as the sole data store and reasoning layer. A Cortex Agent orchestrates
          a 3-stage pipeline — <strong>Retrieval</strong> (Cortex Analyst semantic view + 3 Cortex Search services),
          <strong> Risk Assessment</strong> (polypharmacy scoring UDF), and <strong>Compliance</strong> (policy compliance UDF) —
          surfacing structured evidence at each stage. The React frontend communicates through a FastAPI backend;
          member search and clinical data use direct SQL for sub-second performance.
        </p>
      </div>

      <div className="about-section">
        <h3>Platform</h3>
        <div className="tech-grid">
          <span className="tech-badge">Snowflake Cortex Agent</span>
          <span className="tech-badge">Cortex Analyst</span>
          <span className="tech-badge">Cortex Search</span>
          <span className="tech-badge">Custom UDFs</span>
          <span className="tech-badge">React 18 + TypeScript</span>
          <span className="tech-badge">FastAPI</span>
          <span className="tech-badge">Docker / SPCS</span>
        </div>
      </div>

      <div className="about-disclaimer">
        All data shown is synthetic and used for evaluation purposes. No real patient information is included.
      </div>
    </div>
  );
}
