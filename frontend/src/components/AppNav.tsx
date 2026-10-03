import { useState } from 'react';
import {
  LayoutDashboard, Users, UserPlus, FileText, Settings,
  ClipboardCheck, Shield, ChevronDown, ChevronRight, Activity
} from 'lucide-react';

export type AppPage =
  | 'worklist'
  | 'members'
  | 'member-detail'
  | 'member-studio'
  | 'documents'
  | 'jobs'
  | 'audit'
  | 'settings'
  | 'about';

export type UserRole = 'care_manager' | 'compliance_analyst' | 'ops_analyst' | 'admin';

interface AppNavProps {
  currentPage: AppPage;
  onNavigate: (page: AppPage) => void;
  currentRole: UserRole;
  onRoleChange: (role: UserRole) => void;
  userName: string;
}

interface NavSection {
  label: string;
  items: { key: AppPage; label: string; icon: typeof LayoutDashboard; roles: UserRole[] }[];
}

const NAV_SECTIONS: NavSection[] = [
  {
    label: 'Overview',
    items: [
      { key: 'worklist', label: 'Worklist', icon: LayoutDashboard, roles: ['care_manager', 'ops_analyst', 'admin'] },
    ],
  },
  {
    label: 'Care',
    items: [
      { key: 'members', label: 'Members', icon: Users, roles: ['care_manager', 'compliance_analyst', 'ops_analyst', 'admin'] },
      { key: 'member-studio', label: 'Member Studio', icon: UserPlus, roles: ['admin'] },
    ],
  },
  {
    label: 'Knowledge',
    items: [
      { key: 'documents', label: 'Documents', icon: FileText, roles: ['care_manager', 'compliance_analyst', 'admin'] },
    ],
  },
  {
    label: 'Operations',
    items: [
      { key: 'jobs', label: 'Jobs & Automations', icon: Activity, roles: ['ops_analyst', 'admin'] },
      { key: 'audit', label: 'Audit', icon: ClipboardCheck, roles: ['compliance_analyst', 'admin'] },
    ],
  },
  {
    label: 'Administration',
    items: [
      { key: 'settings', label: 'Settings', icon: Settings, roles: ['admin'] },
    ],
  },
];

const ROLE_LABELS: Record<UserRole, string> = {
  care_manager: 'Care Manager',
  compliance_analyst: 'Compliance Analyst',
  ops_analyst: 'Operations Analyst',
  admin: 'Admin',
};

const ROLE_TOOLTIPS: Partial<Record<AppPage, string>> = {
  worklist: 'Prioritized members requiring attention based on risk signals and recent clinical changes.',
members: 'Search and browse synthetic members and open their complete Member 360 profile.',
    'member-studio': 'Create and manage synthetic members, including demographics, medications, diagnoses, labs, encounters, claims, and member-linked documents.',
  documents: 'Upload and manage clinical, policy, regulatory, and legal documents used for evidence retrieval and cited answers.',
  jobs: 'View scheduled Snowflake jobs, recent executions, processing status, and failures.',
  audit: 'Review AI questions, evidence sources, tools used, guardrail outcomes, and response provenance.',
  settings: 'Manage users, roles, risk configuration, document sources, policies, and application settings.',
};

export function AppNav({ currentPage, onNavigate, currentRole, onRoleChange, userName }: AppNavProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(NAV_SECTIONS.map((s) => s.label)));
  const [showRoleSwitcher, setShowRoleSwitcher] = useState(false);

  const toggleSection = (label: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(label)) next.delete(label); else next.add(label);
      return next;
    });
  };

  return (
    <nav className="app-nav">
      <div className="nav-brand" onClick={() => onNavigate('worklist')}>
        <Shield size={22} className="nav-brand-icon" />
        <span className="nav-brand-text">SnowCare360</span>
      </div>
      <div className="nav-synthetic-badge">Synthetic Data Environment</div>

      <div className="nav-sections">
        {NAV_SECTIONS.map((section) => {
          const visibleItems = section.items.filter((item) => item.roles.includes(currentRole));
          if (visibleItems.length === 0) return null;
          const isExpanded = expandedSections.has(section.label);

          return (
            <div key={section.label} className="nav-section">
              <button className="nav-section-header" onClick={() => toggleSection(section.label)}>
                <span>{section.label}</span>
                {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              </button>
              {isExpanded && (
                <div className="nav-section-items">
                  {visibleItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = currentPage === item.key;
                    const tooltip = ROLE_TOOLTIPS[item.key];
                    return (
                      <button
                        key={item.key}
                        className={`nav-item ${isActive ? 'nav-item-active' : ''}`}
                        onClick={() => onNavigate(item.key)}
                        title={tooltip}
                      >
                        <Icon size={16} />
                        <span>{item.label}</span>
                        {tooltip && <span className="nav-info-icon">ⓘ</span>}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="nav-footer">
        <div className="nav-user-card" onClick={() => setShowRoleSwitcher(!showRoleSwitcher)}>
          <div className="nav-user-avatar">{userName.charAt(0).toUpperCase()}</div>
          <div className="nav-user-info">
            <span className="nav-user-name">{userName}</span>
            <span className="nav-user-role">{ROLE_LABELS[currentRole]}</span>
          </div>
          <ChevronDown size={14} />
        </div>
        {showRoleSwitcher && (
          <div className="nav-role-switcher">
            <div className="role-switcher-label">Demo Role Switcher</div>
            {(Object.keys(ROLE_LABELS) as UserRole[]).map((role) => (
              <button
                key={role}
                className={`role-option ${currentRole === role ? 'role-option-active' : ''}`}
                onClick={() => { onRoleChange(role); setShowRoleSwitcher(false); }}
              >
                {ROLE_LABELS[role]}
              </button>
            ))}
          </div>
        )}
      </div>
    </nav>
  );
}
