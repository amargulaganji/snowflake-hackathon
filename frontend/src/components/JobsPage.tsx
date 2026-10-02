import { useState, useEffect } from 'react';
import { Activity, CheckCircle, XCircle, Clock, RefreshCw, SkipForward, CalendarClock } from 'lucide-react';
import axios from 'axios';

interface Job {
  name: string;
  state: string;
  run_status: string;
  scheduled_time: string;
  completed_time: string | null;
  error_message: string | null;
}

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'SUCCEEDED':
      return <><CheckCircle size={14} className="text-green" /> <span className="text-green">{status}</span></>;
    case 'FAILED':
      return <><XCircle size={14} className="text-red" /> <span className="text-red">{status}</span></>;
    case 'SKIPPED':
      return <><SkipForward size={14} style={{ color: '#888' }} /> <span style={{ color: '#888' }}>SKIPPED (no new data)</span></>;
    case 'SCHEDULED':
      return <><CalendarClock size={14} style={{ color: '#3b82f6' }} /> <span style={{ color: '#3b82f6' }}>SCHEDULED</span></>;
    default:
      return <><Clock size={14} /> <span>{status}</span></>;
  }
}

export function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get('/admin/jobs');
      setJobs(data);
    } catch { setJobs([]); }
    setLoading(false);
  };

  useEffect(() => { fetchJobs(); }, []);

  return (
    <div className="page-container">
      <div className="page-header">
        <h2><Activity size={20} /> Jobs &amp; Automations</h2>
        <p className="page-subtitle">View scheduled Snowflake tasks, recent executions, and processing status</p>
      </div>

      <div className="page-toolbar">
        <button className="toolbar-btn" onClick={fetchJobs}><RefreshCw size={14} /> Refresh</button>
      </div>

      <div className="jobs-section">
        <h3>Scheduled Tasks</h3>
        <div className="job-card">
          <div className="job-header">
            <Clock size={16} />
            <span className="job-name">RISK_DELTA_NIGHTLY_TASK</span>
            <span className="status-pill status-active">ACTIVE</span>
          </div>
          <div className="job-details">
            <span>Schedule: Daily at 2:00 AM UTC</span>
            <span>Warehouse: COPILOT_WH</span>
            <span>Action: CALL REFRESH_RISK_DELTAS()</span>
          </div>
        </div>
        <div className="job-card">
          <div className="job-header">
            <Clock size={16} />
            <span className="job-name">DOCUMENT_PROCESSING_TASK</span>
            <span className="status-pill status-active">ACTIVE</span>
          </div>
          <div className="job-details">
            <span>Schedule: Every 5 minutes (when stream has data)</span>
            <span>Warehouse: COPILOT_WH</span>
            <span>Action: Update SEARCH_INDEX_STATUS from DOCUMENT_CHANGE_STREAM</span>
          </div>
        </div>
      </div>

      <div className="jobs-section">
        <h3>Recent Executions</h3>
        {loading ? (
          <div className="page-loading">Loading job history...</div>
        ) : jobs.length === 0 ? (
          <div className="page-empty"><p>No recent executions found for CLINICAL_COPILOT tasks.</p></div>
        ) : (
          <table className="detail-table">
            <thead>
              <tr><th>Task</th><th>Status</th><th>Scheduled</th><th>Completed</th><th>Error</th></tr>
            </thead>
            <tbody>
              {jobs.map((j, i) => (
                <tr key={i}>
                  <td className="td-primary">{j.name}</td>
                  <td><StatusIcon status={j.run_status} /></td>
                  <td>{j.scheduled_time || '\u2014'}</td>
                  <td>{j.completed_time || '\u2014'}</td>
                  <td>{j.error_message || '\u2014'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
