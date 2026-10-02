import { useState, useCallback } from 'react';
import { askAgent } from '../api/client';
import type { AskResponse } from '../types';

export function useAgent() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<AskResponse | null>(null);

  const ask = useCallback(async (
    memberId: string,
    question: string,
    history?: { role: string; content: string }[],
  ) => {
    setLoading(true);
    setError(null);
    setResponse(null);
    try {
      const data = await askAgent({ member_id: memberId, question, history });
      setResponse(data);
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Request failed';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return { ask, loading, error, response, clearError };
}
