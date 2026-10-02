import { useState, useEffect } from 'react';
import { getMemberDetail } from '../api/client';
import type { MemberDetail } from '../types';

export function useMemberDetail(memberId: string | null) {
  const [detail, setDetail] = useState<MemberDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!memberId) {
      setDetail(null);
      setError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    getMemberDetail(memberId)
      .then((data) => {
        if (cancelled) return;
        // Ensure arrays exist even if agent returns incomplete data
        const safe: MemberDetail = {
          member_id: data.member_id || memberId,
          first_name: data.first_name || '',
          last_name: data.last_name || '',
          age: data.age ?? 0,
          gender: data.gender || '',
          plan_type: data.plan_type || '',
          risk_flags: Array.isArray(data.risk_flags) ? data.risk_flags : [],
          dob: data.dob || '',
          enrollment_date: data.enrollment_date || '',
          pcp_name: data.pcp_name || '',
          encounters: Array.isArray(data.encounters) ? data.encounters : [],
          medications: Array.isArray(data.medications) ? data.medications : [],
          diagnoses: Array.isArray(data.diagnoses) ? data.diagnoses : [],
          labs: Array.isArray(data.labs) ? data.labs : [],
          sources: Array.isArray(data.sources) ? data.sources : [],
          claims: Array.isArray(data.claims) ? data.claims : [],
          attachments: Array.isArray(data.attachments) ? data.attachments : [],
        };
        setDetail(safe);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load member details');
          setDetail(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [memberId]);

  return { detail, loading, error };
}
