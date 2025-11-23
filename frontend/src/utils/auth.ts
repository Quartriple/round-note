/**
 * 인증 관련 유틸리티 함수
 * httpOnly Cookie 기반 인증 시스템
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * 서버에 현재 사용자 정보를 요청하여 인증 상태 확인
 * @returns 인증된 경우 사용자 정보, 아니면 null
 */
export async function checkAuth(): Promise<{ id: string; email: string; name: string } | null> {
  try {
    const response = await fetch(`${API_URL}/api/v1/auth/me`, {
      method: 'GET',
      credentials: 'include', // httpOnly Cookie 전송
    });

    if (response.ok) {
      const data = await response.json();
      // 백엔드 응답 형식을 프론트엔드 형식으로 변환
      return {
        id: data.user_id || data.USER_ID,
        email: data.email || data.EMAIL,
        name: data.name || data.NAME,
      };
    }

    return null;
  } catch (error) {
    console.error('Authentication check failed:', error);
    return null;
  }
}

/**
 * 로그아웃 처리
 */
export async function logout(): Promise<void> {
  try {
    await fetch(`${API_URL}/api/v1/auth/logout`, {
      method: 'POST',
      credentials: 'include', // httpOnly Cookie 전송
    });
  } catch (error) {
    console.error('Logout failed:', error);
  }
}
