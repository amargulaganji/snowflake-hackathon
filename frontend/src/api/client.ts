import axios from 'axios';
import type { MemberSummary, MemberDetail, AskRequest, AskResponse } from '../types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
});

export async function searchMembers(query: string): Promise<MemberSummary[]> {
  const { data } = await api.get<MemberSummary[]>('/members', {
    params: { q: query },
  });
  return data;
}

export async function getTopRiskMembers(): Promise<MemberSummary[]> {
  const { data } = await api.get<MemberSummary[]>('/members/top-risk', {
    params: { limit: 10 },
  });
  return data;
}

export async function getMemberDetail(memberId: string): Promise<MemberDetail> {
  const { data } = await api.get<MemberDetail>(`/members/${memberId}`);
  return data;
}

export async function getMemberRiskExplanation(memberId: string): Promise<any> {
  const { data } = await api.get(`/members/${memberId}/risk-explanation`);
  return data;
}

export async function askAgent(request: AskRequest): Promise<AskResponse> {
  const { data } = await api.post<AskResponse>('/ask', {
    member_id: request.member_id,
    question: request.question,
    history: request.history || [],
  });
  return data;
}
