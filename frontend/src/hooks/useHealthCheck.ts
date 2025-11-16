import { useState, useEffect } from 'react';

// Render 환경 변수를 읽어 API 주소를 설정합니다.
const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const useHealthCheck = () => {
    // 1. API 응답을 저장할 상태 정의
    const [healthCheckData, setHealthCheckData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // 2. 컴포넌트 로드 시 헬스 체크 API 호출 (App.js의 로직 재활용)
    useEffect(() => {
        fetch(`${apiUrl}/health-check`)
            .then(response => {
                if (!response.ok) {
                    // HTTP 503 등 오류 시, JSON 데이터(상세 오류)를 파싱
                    return response.json().then(errData => {
                        throw new Error(JSON.stringify(errData, null, 2));
                    });
                }
                return response.json();
            })
            .then(data => {
                setHealthCheckData(data);
                setLoading(false);
            })
            .catch(err => {
                setError(err.message);
                setLoading(false);
            });
    }, []);

    // 3. 상태와 데이터를 반환합니다.
    return { healthCheckData, loading, error, apiUrl };
};

export default useHealthCheck;