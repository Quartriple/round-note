/**
 * 회의(Meeting) API 서비스
 * 백엔드 /api/v1/meetings 엔드포인트와 통신
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// 토큰을 로컬스토리지에서 가져오는 헬퍼 함수
const getAuthToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
};

const clearAuth = () => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('access_token');
    // keep refresh_token handling for future implementation
    // localStorage.removeItem('refresh_token');
  }
};

// 공통 헤더 생성
const getHeaders = (): HeadersInit => {
  const token = getAuthToken();
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
};

// Small helper error class so callers can detect auth errors reliably
export class AuthError extends Error {
  constructor(message?: string) {
    super(message || 'Unauthorized');
    this.name = 'AuthError';
  }
}

// Centralized response handling: handles 401 uniformly
const handleResponse = async (response: Response) => {
  if (response.ok) return response;

  // Try to parse JSON body safely
  const body = await response.json().catch(() => ({ detail: response.statusText || 'Request failed' }));

  if (response.status === 401) {
    // clear local tokens and throw marker AuthError
    clearAuth();
    throw new AuthError(body.detail || '유효하지 않은 인증 토큰입니다.');
  }

  throw new Error(body.detail || `Request failed with status ${response.status}`);
};

// API 응답 타입 정의
export interface MeetingResponse {
  meeting_id: string;
  title: string;
  purpose?: string;
  creator_id: string;
  status?: string;
  start_dt: string;
  end_dt?: string;
  location?: string;
}

export interface CreateMeetingRequest {
  title: string;
  purpose?: string;
  is_realtime?: boolean;
}

export interface UpdateMeetingRequest {
  title?: string;
  purpose?: string;
  status?: string;
}

export interface EndMeetingRequest {
  status?: string;
  ended_at?: string;
  content?: string;
  audio_url?: string;
}

/**
 * 회의 생성
 */
export const createMeeting = async (data: CreateMeetingRequest): Promise<MeetingResponse> => {
  const response = await fetch(`${API_URL}/api/v1/meetings/`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(data),
  });

  await handleResponse(response);
  return response.json();
};

/**
 * 회의 목록 조회
 */
export const listMeetings = async (skip: number = 0, limit: number = 100): Promise<MeetingResponse[]> => {
  const response = await fetch(`${API_URL}/api/v1/meetings/?skip=${skip}&limit=${limit}`, {
    method: 'GET',
    headers: getHeaders(),
  });

  await handleResponse(response);
  return response.json();
};

/**
 * 회의 상세 조회
 */
export const getMeeting = async (meetingId: string): Promise<MeetingResponse> => {
  const response = await fetch(`${API_URL}/api/v1/meetings/${meetingId}`, {
    method: 'GET',
    headers: getHeaders(),
  });

  await handleResponse(response);
  return response.json();
};

/**
 * 회의 수정
 */
export const updateMeeting = async (meetingId: string, data: UpdateMeetingRequest): Promise<MeetingResponse> => {
  const response = await fetch(`${API_URL}/api/v1/meetings/${meetingId}`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify(data),
  });

  await handleResponse(response);
  return response.json();
};

/**
 * 회의 삭제
 */
export const deleteMeeting = async (meetingId: string): Promise<void> => {
  const response = await fetch(`${API_URL}/api/v1/meetings/${meetingId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });

  await handleResponse(response);
  return;
};

/**
 * 회의 종료 (요약 및 액션 아이템 자동 생성)
 */
export const endMeeting = async (meetingId: string, data?: EndMeetingRequest): Promise<{ 
  message: string; 
  meeting_id: string; 
  status: string; 
  end_dt?: string;
  content?: string;
  audio_url?: string;
  summary?: string;
  action_items?: Array<{task: string; assignee: string; deadline: string}>;
}> => {
  const response = await fetch(`${API_URL}/api/v1/meetings/${meetingId}/end`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(data || { status: 'COMPLETED', ended_at: new Date().toISOString() }),
  });

  await handleResponse(response);
  return response.json();
};

/**
 * 회의 요약 조회
 */
export const getMeetingSummary = async (meetingId: string): Promise<{
  summary_id: string;
  meeting_id: string;
  format: string;
  content: string;
  translated_content?: string;
  created_dt: string;
}> => {
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
 * 회의 액션 아이템 조회
 */
export const getMeetingActionItems = async (meetingId: string): Promise<Array<{
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
}>> => {
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
 * 회의 내용 번역 (요약 또는 전사)
 */
export const translateMeetingContent = async (
  meetingId: string, 
  contentType: 'summary' | 'transcript',
  targetLang: string = 'en'
): Promise<{
  meeting_id: string;
  content_type: string;
  translated_text: string;
  cached: boolean;
}> => {
  const response = await fetch(
    `${API_URL}/api/v1/reports/${meetingId}/translate?content_type=${contentType}&target_lang=${targetLang}`, 
    {
      method: 'POST',
      headers: getHeaders(),
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to translate' }));
    throw new Error(error.detail || 'Failed to translate');
  }

  return response.json();
};
