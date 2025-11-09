import React, { useState, useEffect } from 'react';
import logo from './logo.svg';
import './App.css';

function App() {
  // 1. API 응답을 저장할 state 생성
  const [healthCheckData, setHealthCheckData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 2. Render에 설정한 API 서버 주소 읽어오기
  //    (Render 'Static Site'의 환경 변수에 REACT_APP_API_URL='...' 등록 필요)
  const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000'; // 기본값

  // 3. 컴포넌트가 로드될 때 '한 번만' /health-check API 호출
  useEffect(() => {
    fetch(`${apiUrl}/health-check`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        // 성공 시, state에 JSON 데이터 저장
        setHealthCheckData(data);
        setLoading(false);
      })
      .catch(err => {
        // 실패 시, state에 에러 메시지 저장
        setError(err.message);
        setLoading(false);
      });
  }, [apiUrl]); // apiUrl이 변경될 때만 재실행 (사실상 1번만 실행됨)

  // 4. API 호출 상태에 따라 다른 UI 표시
  const renderHealthCheck = () => {
    if (loading) {
      return <p>Loading Health Check from {apiUrl}...</p>;
    }
    if (error) {
      return <p style={{ color: 'red' }}>Error: {error}</p>;
    }
    if (healthCheckData) {
      // JSON 데이터를 보기 좋게 문자열로 변환
      return <pre>{JSON.stringify(healthCheckData, null, 2)}</pre>;
    }
    return null;
  };

  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <h1>Round Note - Sprint 0 Test</h1>
        
        <h2>API Health Check Result:</h2>
        {/* API 호출 결과를 여기에 렌더링 */}
        {renderHealthCheck()}
      </header>
    </div>
  );
}

export default App;