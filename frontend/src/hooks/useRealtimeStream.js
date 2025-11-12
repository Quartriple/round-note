import { useState, useRef, useCallback, useEffect } from 'react';
import { useMicVAD } from '@ricky0123/vad-react';

// WebSocket 설정 관련 전역 상수
const WS_URL = process.env.REACT_APP_API_URL ? 
    `ws${process.env.REACT_APP_API_URL.substring(4)}/api/v1/realtime/ws` : 
    'ws://localhost:8000/api/v1/realtime/ws';

// 오디오 설정 (Deepgram 요구사항에 맞춤)
const AUDIO_CONFIG = {
    sampleRate: 16000,
    channel: 1,
    bufferSize: 4096,
};

const useRealtimeStream = () => {
    // 1. 상태 정의
    const [isRecording, setIsRecording] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [partialText, setPartialText] = useState('');
    const [translation, setTranslation] = useState('');

    // 2. Mutable 객체 참조
    const wsRef = useRef(null);
    const isRecordingRef = useRef(false); // 최신 isRecording 상태를 추적

    // VAD 설정 - pause/listening 확인
    const vad = useMicVAD({
        sampleRate: AUDIO_CONFIG.sampleRate,
        onAudioData: (audioDataAsInt16Array) => {
            if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                wsRef.current.send(audioDataAsInt16Array.buffer);
            }
        },
        onSpeechStart: () => {
            console.log("VAD: Speech Started");
        },
        onSpeechEnd: () => {
            console.log("VAD: Speech End");
        },
    });

    // isRecording 변경 시 ref 동기화
    useEffect(() => {
        isRecordingRef.current = isRecording;
    }, [isRecording]);

    // 리소스 정리 함수
    const cleanupResources = useCallback(() => {
        console.log("리소스 정리 시작");
        
        // VAD 중지 - pause 메서드 사용
        if (vad && typeof vad.pause === 'function') {
            try {
                vad.pause();
                console.log("VAD 중지됨");
            } catch (e) {
                console.error("VAD 중지 오류:", e);
            }
        }

        // WebSocket 연결 닫기
        if (wsRef.current) {
            try {
                // 핸들러 제거
                wsRef.current.onmessage = null;
                wsRef.current.onclose = null;
                wsRef.current.onerror = null;
                
                if (wsRef.current.readyState === WebSocket.OPEN || 
                    wsRef.current.readyState === WebSocket.CONNECTING) {
                    wsRef.current.close();
                }
                wsRef.current = null;
                console.log("WebSocket 정리됨");
            } catch (e) {
                console.error("WebSocket 정리 오류:", e);
            }
        }
    }, [vad]);

    // 녹음 시작
    const startRecording = useCallback(async () => {
        if (vad.loading) {
            console.log("VAD 로딩 중...");
            return;
        }

        try {
            const wsUrl = WS_URL + "?translate=true";
            console.log("WebSocket 연결 시도:", wsUrl);
            console.log("환경변수 API_URL:", process.env.REACT_APP_API_URL);
            
            const ws = new WebSocket(wsUrl);
            wsRef.current = ws;

            // WebSocket 연결 상태 모니터링
            console.log("WebSocket readyState:", ws.readyState);
            // 0: CONNECTING, 1: OPEN, 2: CLOSING, 3: CLOSED

            // WebSocket 연결 대기
            await new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    console.error("WebSocket 연결 타임아웃 (5초)");
                    reject(new Error("WebSocket 연결 타임아웃"));
                }, 5000);

                ws.onopen = () => {
                    clearTimeout(timeout);
                    console.log("✅ WebSocket 연결 성공!");
                    console.log("WebSocket readyState:", ws.readyState);
                    resolve();
                };
                
                ws.onerror = (error) => {
                    clearTimeout(timeout);
                    console.error("❌ WebSocket 연결 오류:", error);
                    console.error("WebSocket readyState:", ws.readyState);
                    reject(new Error("WebSocket 연결 실패"));
                };
            });

            // WebSocket 메시지 핸들러 설정
            ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    
                    switch (message.type) {
                        case 'partial_transcript':
                            setPartialText(message.text);
                            break;
                            
                        case 'final_transcript':
                            setTranscript(prev => {
                                const newText = prev ? prev + '\n' + message.text : message.text;
                                return newText;
                            });
                            setPartialText('');
                            break;
                            
                        case 'translation':
                            setTranslation(message.translated_text);
                            break;
                            
                        case 'error':
                            console.error("Server Error:", message.message);
                            setPartialText(`[ERROR]: ${message.message}`);
                            break;
                            
                        default:
                            console.warn("Unknown message type:", message.type);
                    }
                } catch (e) {
                    console.error("메시지 파싱 오류:", e);
                }
            };

            // WebSocket 종료 핸들러
            ws.onclose = () => {
                console.log("WebSocket 연결 종료");
                if (isRecordingRef.current) {
                    setIsRecording(false);
                    setTranscript(prev => prev + '\n[서버 연결 종료]');
                }
            };

            // VAD 시작 - start 메서드 사용
            if (typeof vad.start === 'function') {
                vad.start();
                console.log("VAD 시작됨");
            }

            setIsRecording(true);
            setTranscript('🎙️ 실시간 전사를 시작합니다.');

        } catch (e) {
            console.error("녹음 시작 오류:", e);
            cleanupResources();
            setIsRecording(false);
            setTranscript('❌ 녹음 시작 실패: ' + e.message);
        }
    }, [vad, cleanupResources]);

    // 녹음 중지
    const stopRecording = useCallback(() => {
        if (!isRecording) {
            console.log("이미 녹음이 중지됨");
            return;
        }
        
        console.log("녹음 중지 시작");
        cleanupResources();

        setIsRecording(false);
        setPartialText('');
        setTranscript(prev => prev + '\n[녹음 종료]');
        console.log("녹음 중지 완료");

    }, [isRecording, cleanupResources]);

    // 컴포넌트 언마운트 시 정리
    useEffect(() => {
        return () => {
            console.log("컴포넌트 언마운트 - 리소스 정리");
            if (wsRef.current) {
                wsRef.current.onmessage = null;
                wsRef.current.onclose = null;
                wsRef.current.onerror = null;
                if (wsRef.current.readyState === WebSocket.OPEN) {
                    wsRef.current.close();
                }
            }
        };
    }, []);

    return {
        isRecording: isRecording || vad.loading,
        transcript,
        partialText,
        translation,
        startRecording,
        stopRecording,
        vadLoading: vad.loading,
    };
};

export default useRealtimeStream;