import { useState } from 'react';
import { useMemberSearch } from '../hooks/useMemberSearch';
import { Avatar } from './Avatar';
import type { MemberSummary } from '../types';

interface MemberSearchProps {
  onSelect: (member: MemberSummary) => void;
}

export function MemberSearch({ onSelect }: MemberSearchProps) {
  const [query, setQuery] = useState('');
  const { results, loading, error } = useMemberSearch(query);
  const showNoResults = query.length >= 2 && !loading && !error && results.length === 0;

  return (
    <div className="member-search">
      <input
        type="text"
        className="search-input"
        placeholder="Search members by name or ID..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      {loading && <div className="search-loading">Searching...</div>}
      {error && <div className="search-error">{error}</div>}
      {showNoResults && <div className="search-no-results">No members match "{query}"</div>}
      <ul className="search-results">
        {results.map((member) => (
          <li key={member.member_id} className="search-result-item" onClick={() => { onSelect(member); setQuery(''); }}>
            <Avatar firstName={member.first_name} lastName={member.last_name} memberId={member.member_id} size={32} />
            <div>
              <span className="member-name">{member.first_name} {member.last_name}</span>
              <span className="member-meta">{member.age}y · {member.gender} · {member.plan_type}</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
