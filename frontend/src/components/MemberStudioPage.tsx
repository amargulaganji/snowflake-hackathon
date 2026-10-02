import { useState } from 'react';
import { UserPlus, Zap, User, Loader } from 'lucide-react';
import axios from 'axios';

const CONDITIONS = ['CKD', 'Diabetes', 'Heart Failure', 'Hypertension', 'COPD', 'Atrial Fibrillation', 'Obesity', 'Depression'];
const INCLUDES = ['Medications', 'Labs', 'Encounters', 'Claims', 'Clinical Notes', 'Abnormal Results', 'Contradiction Scenario'];

export function MemberStudioPage() {
  const [mode, setMode] = useState<'manual' | 'generate'>('generate');
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  // Generate form state
  const [ageMin, setAgeMin] = useState(70);
  const [ageMax, setAgeMax] = useState(90);
  const [selectedConditions, setSelectedConditions] = useState<Set<string>>(new Set(['CKD', 'Diabetes']));
  const [complexity, setComplexity] = useState<'low' | 'moderate' | 'high'>('high');
  const [includes, setIncludes] = useState<Set<string>>(new Set(INCLUDES.slice(0, 5)));

  // Manual form state
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [age, setAge] = useState(75);
  const [gender, setGender] = useState('Male');
  const [planType, setPlanType] = useState('Medicare Advantage');
  const [pcpName, setPcpName] = useState('');

  const toggleCondition = (c: string) => {
    setSelectedConditions((prev) => { const n = new Set(prev); if (n.has(c)) n.delete(c); else n.add(c); return n; });
  };
  const toggleInclude = (i: string) => {
    setIncludes((prev) => { const n = new Set(prev); if (n.has(i)) n.delete(i); else n.add(i); return n; });
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setResult(null);
    try {
      const { data } = await axios.post('/studio/generate', {
        age_min: ageMin,
        age_max: ageMax,
        conditions: Array.from(selectedConditions),
        complexity,
        includes: Array.from(includes),
      });
      setResult(`Created synthetic member ${data.member_id}: ${data.first_name} ${data.last_name}`);
    } catch (err) {
      setResult('Generation failed. Check backend logs.');
    }
    setGenerating(false);
  };

  const handleManualCreate = async () => {
    if (!firstName || !lastName) return;
    setGenerating(true);
    setResult(null);
    try {
      const { data } = await axios.post('/studio/members', {
        first_name: firstName, last_name: lastName, age, gender, plan_type: planType, pcp_name: pcpName, risk_flags: Array.from(selectedConditions),
      });
      setResult(`Created synthetic member ${data.member_id}: ${data.first_name} ${data.last_name}`);
    } catch { setResult('Creation failed.'); }
    setGenerating(false);
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h2><UserPlus size={20} /> Member Studio</h2>
        <p className="page-subtitle">Create and manage synthetic members with demographics, medications, diagnoses, labs, encounters, claims, and documents</p>
      </div>

      <div className="studio-mode-tabs">
        <button className={`studio-tab ${mode === 'generate' ? 'studio-tab-active' : ''}`} onClick={() => setMode('generate')}>
          <Zap size={14} /> Generate with CoCo
        </button>
        <button className={`studio-tab ${mode === 'manual' ? 'studio-tab-active' : ''}`} onClick={() => setMode('manual')}>
          <User size={14} /> Manual Entry
        </button>
      </div>

      {mode === 'generate' ? (
        <div className="studio-form">
          <div className="form-row">
            <label>Age Range</label>
            <div className="form-inline">
              <input type="number" value={ageMin} onChange={(e) => setAgeMin(+e.target.value)} min={0} max={120} className="form-input form-input-sm" />
              <span>to</span>
              <input type="number" value={ageMax} onChange={(e) => setAgeMax(+e.target.value)} min={0} max={120} className="form-input form-input-sm" />
            </div>
          </div>

          <div className="form-row">
            <label>Conditions</label>
            <div className="checkbox-grid">
              {CONDITIONS.map((c) => (
                <label key={c} className="checkbox-label">
                  <input type="checkbox" checked={selectedConditions.has(c)} onChange={() => toggleCondition(c)} />
                  <span>{c}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="form-row">
            <label>Complexity</label>
            <div className="radio-group">
              {(['low', 'moderate', 'high'] as const).map((level) => (
                <label key={level} className="radio-label">
                  <input type="radio" name="complexity" checked={complexity === level} onChange={() => setComplexity(level)} />
                  <span>{level.charAt(0).toUpperCase() + level.slice(1)}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="form-row">
            <label>Include</label>
            <div className="checkbox-grid">
              {INCLUDES.map((i) => (
                <label key={i} className="checkbox-label">
                  <input type="checkbox" checked={includes.has(i)} onChange={() => toggleInclude(i)} />
                  <span>{i}</span>
                </label>
              ))}
            </div>
          </div>

          <button className="primary-btn" onClick={handleGenerate} disabled={generating}>
            {generating ? <><Loader size={14} className="spin" /> Generating...</> : <><Zap size={14} /> Generate Synthetic Member with CoCo</>}
          </button>
        </div>
      ) : (
        <div className="studio-form">
          <div className="form-grid-2">
            <div className="form-row"><label>First Name</label><input className="form-input" value={firstName} onChange={(e) => setFirstName(e.target.value)} /></div>
            <div className="form-row"><label>Last Name</label><input className="form-input" value={lastName} onChange={(e) => setLastName(e.target.value)} /></div>
            <div className="form-row"><label>Age</label><input className="form-input" type="number" value={age} onChange={(e) => setAge(+e.target.value)} /></div>
            <div className="form-row"><label>Gender</label>
              <select className="form-input" value={gender} onChange={(e) => setGender(e.target.value)}>
                <option>Male</option><option>Female</option><option>Other</option>
              </select>
            </div>
            <div className="form-row"><label>Plan Type</label><input className="form-input" value={planType} onChange={(e) => setPlanType(e.target.value)} /></div>
            <div className="form-row"><label>PCP Name</label><input className="form-input" value={pcpName} onChange={(e) => setPcpName(e.target.value)} /></div>
          </div>

          <div className="form-row">
            <label>Conditions / Risk Flags</label>
            <div className="checkbox-grid">
              {CONDITIONS.map((c) => (
                <label key={c} className="checkbox-label">
                  <input type="checkbox" checked={selectedConditions.has(c)} onChange={() => toggleCondition(c)} />
                  <span>{c}</span>
                </label>
              ))}
            </div>
          </div>

          <button className="primary-btn" onClick={handleManualCreate} disabled={generating}>
            {generating ? 'Creating...' : 'Create Member'}
          </button>
        </div>
      )}

      {result && <div className="studio-result">{result}</div>}
    </div>
  );
}
