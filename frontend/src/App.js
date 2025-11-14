import React from 'react';
import './App.css';

import MeetingPage from './pages/MeetingPage'; 

function App() {
    return (
        <div className="App">
            {/* 현재는 라우팅이 하나뿐이므로, 바로 MeetingPage를 렌더링합니다. */}
            <MeetingPage /> 
        </div>
    );
}

export default App;