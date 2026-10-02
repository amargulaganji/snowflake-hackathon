import { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Users, Shield } from 'lucide-react';
import axios from 'axios';

interface AppUser {
  user_id: string;
  username: string;
  display_name: string;
  role: string;
  created_at: string;
}

export function SettingsPage() {
  const [users, setUsers] = useState<AppUser[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get('/admin/users')
      .then(({ data }) => setUsers(data))
      .catch(() => setUsers([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page-container">
      <div className="page-header">
        <h2><SettingsIcon size={20} /> Settings</h2>
        <p className="page-subtitle">Manage users, roles, risk configuration, document sources, and application settings</p>
      </div>

      <div className="settings-section">
        <h3><Users size={16} /> Users &amp; Roles</h3>
        {loading ? (
          <div className="page-loading">Loading users...</div>
        ) : (
          <table className="detail-table">
            <thead><tr><th>User</th><th>Username</th><th>Role</th><th>Created</th></tr></thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.user_id}>
                  <td className="td-primary">{u.display_name}</td>
                  <td>{u.username}</td>
                  <td><span className="doc-type-badge">{u.role}</span></td>
                  <td>{u.created_at?.slice(0, 10)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="settings-section">
        <h3><Shield size={16} /> Application Info</h3>
        <div className="settings-info-grid">
          <div className="settings-info-item"><span className="info-label">Database</span><span>CLINICAL_COPILOT.CORE</span></div>
          <div className="settings-info-item"><span className="info-label">Warehouse</span><span>COPILOT_WH</span></div>
          <div className="settings-info-item"><span className="info-label">Agent</span><span>CLINICAL_COPILOT_AGENT</span></div>
          <div className="settings-info-item"><span className="info-label">Model</span><span>claude-4-sonnet</span></div>
          <div className="settings-info-item"><span className="info-label">Search Services</span><span>3 (Clinical Notes, Policy Docs, Drug Interactions)</span></div>
          <div className="settings-info-item"><span className="info-label">Nightly Task</span><span>RISK_DELTA_NIGHTLY_TASK (2 AM UTC)</span></div>
        </div>
      </div>
    </div>
  );
}
