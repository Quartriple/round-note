/**
 * Reports API 서비스
 * 백엔드 /api/v1/reports 엔드포인트와 통신
 * LLM 기반 요약, 액션 아이템 추출 등을 처리
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// 토큰을 로컬스토리지에서 가져오는 헬퍼 함수
const getAuthToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
};

// 공통 헤더 생성
const getHeaders = (): HeadersInit => {
  const token = getAuthToken();
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
};

// ==================== 타입 정의 ====================

export interface SummaryResponse {
  summary_id: string;
  meeting_id: string;
  format: string;
  content: string;
  created_dt: string;
}

export interface ActionItemResponse {
  item_id: string;
  meeting_id: string;
  title: string;
  description?: string;
  due_dt?: string;
  priority?: string;
  status: string;
  assignee_id?: string;
  external_tool?: string;
  created_dt: string;
  updated_dt?: string;
}

export interface FullReportResponse {
  meeting_id: string;
  summary: SummaryResponse | null;
  action_items: ActionItemResponse[];
  full_transcript: string | null;
}

export interface RegenerateResponse {
  message: string;
  meeting_id: string;
  summary: string;
  action_items_count: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  answer: string;
  sources?: string[];
}

// ==================== API 함수 ====================

/**
 * 회의 요약 조회
 */
export const getMeetingSummary = async (meetingId: string): Promise<SummaryResponse> => {
  const response = await fetch(`${API_URL}/api/v1/reports/${meetingId}/summary`, {
    method: 'GET',
    headers: getHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch summary' }));
    throw new Error(error.detail || 'Failed to fetch summary');
  }

  return response.json();
};

/**
 * 액션 아이템 목록 조회
 */
export const getMeetingActionItems = async (meetingId: string): Promise<ActionItemResponse[]> => {
  const response = await fetch(`${API_URL}/api/v1/reports/${meetingId}/action-items`, {
    method: 'GET',
    headers: getHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch action items' }));
    throw new Error(error.detail || 'Failed to fetch action items');
  }

  return response.json();
};

/**
 * 전체 보고서 조회 (요약 + 액션 아이템 + 전사 내용)
 */
export const getFullReport = async (meetingId: string): Promise<FullReportResponse> => {
  const response = await fetch(`${API_URL}/api/v1/reports/${meetingId}/full`, {
    method: 'GET',
    headers: getHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch full report' }));
    throw new Error(error.detail || 'Failed to fetch full report');
  }

  return response.json();
};

/**
 * 요약 및 액션 아이템 재생성 (LLM 호출)
 */
export const regenerateSummary = async (meetingId: string): Promise<RegenerateResponse> => {
  const response = await fetch(`${API_URL}/api/v1/reports/${meetingId}/regenerate`, {
    method: 'POST',
    headers: getHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to regenerate summary' }));
    throw new Error(error.detail || 'Failed to regenerate summary');
  }

  return response.json();
};

/**
 * 회의 내용 검색 (RAG 기반) - TODO: 백엔드 구현 후 활성화
 */
export const searchMeetingContent = async (
  meetingId: string, 
  query: string
): Promise<{ results: string[] }> => {
  const response = await fetch(
    `${API_URL}/api/v1/reports/${meetingId}/search?query=${encodeURIComponent(query)}`, 
    {
      method: 'GET',
      headers: getHeaders(),
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Search failed' }));
    throw new Error(error.detail || 'Search failed');
  }

  return response.json();
};

/**
 * 챗봇 질문 (회의 내용 기반 Q&A)
 */
export const chatWithMeeting = async (
  meetingId: string,
  message: string,
  history: ChatMessage[] = []
): Promise<ChatResponse> => {
  const response = await fetch(`${API_URL}/api/v1/reports/${meetingId}/chat`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({
      message,
      history,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Chat failed' }));
    throw new Error(error.detail || 'Chat failed');
  }

  return response.json();
};

/**
 * Jira로 액션 아이템 내보내기
 */
export const pushToJira = async (meetingId: string): Promise<{ created: any[]; count: number }> => {
  const response = await fetch(`${API_URL}/api/v1/reports/${meetingId}/action-items/to-jira`, {
    method: 'POST',
    headers: getHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to push to Jira' }));
    throw new Error(error.detail || 'Failed to push to Jira');
  }

  return response.json();
};

/**
 * Notion으로 보고서 내보내기
 */
export const pushToNotion = async (meetingId: string): Promise<any> => {
  const response = await fetch(`${API_URL}/api/v1/reports/${meetingId}/report/to-notion`, {
    method: 'POST',
    headers: getHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to push to Notion' }));
    throw new Error(error.detail || 'Failed to push to Notion');
  }

  return response.json();
};
