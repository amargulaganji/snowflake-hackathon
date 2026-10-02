import type { MemberSummary } from '../types';
import { RiskBadge } from './RiskBadge';
import { Avatar } from './Avatar';

interface MemberProfileProps {
  member: MemberSummary;
}

export function MemberProfile({ member }: MemberProfileProps) {
  return (
    <div className="member-profile card">
      <div className="profile-header-row">
        <Avatar firstName={member.first_name} lastName={member.last_name} memberId={member.member_id} size={44} />
        <div>
          <h3 className="profile-name">{member.first_name} {member.last_name}</h3>
          <span className="profile-id">{member.member_id}</span>
        </div>
      </div>
      <div className="profile-details">
        <div className="profile-field">
          <span className="field-label">Age</span>
          <span className="field-value">{member.age}</span>
        </div>
        <div className="profile-field">
          <span className="field-label">Gender</span>
          <span className="field-value">{member.gender}</span>
        </div>
        <div className="profile-field">
          <span className="field-label">Plan</span>
          <span className="field-value">{member.plan_type}</span>
        </div>
      </div>
      {member.risk_flags.length > 0 && (
        <div className="profile-risks">
          {member.risk_flags.map((flag) => (<RiskBadge key={flag} level={flag} />))}
        </div>
      )}
    </div>
  );
}
