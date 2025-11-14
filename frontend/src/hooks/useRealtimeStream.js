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

function float32ToInt16(float32Array) {
    let int16Array = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
        // -1.0에서 1.0 범위로 클리핑
        let s = Math.max(-1, Math.min(1, float32Array[i]));
        // 16비트 정수로 변환
        int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return int16Array;
}

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
    const { loading: vadLoading, start: vadStart, pause: vadPause } = useMicVAD({
        model: "v5",
        sampleRate: AUDIO_CONFIG.sampleRate,
        baseAssetPath: '/',
        onnxWASMBasePath: 'https://cdn.jsdelivr.net/npm/onnxruntime-web@1.23.2/dist/',
        onFrameProcessed: (probs, frame) => {
            const isSpeech = probs.isSpeech > 0.6;
            // console.log(`VAD Frame Processed - isSpeech: ${isSpeech}, Probability: ${probs.isSpeech.toFixed(3)}`);
            const int16Frame = float32ToInt16(frame);
            
            if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && int16Frame.buffer.byteLength > 0) {
                console.log("전송 데이터 타입:", int16Frame.buffer instanceof ArrayBuffer);
                wsRef.current.send(int16Frame.buffer);
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
        try {
            vadPause();
            console.log("VAD 중지됨");
        } catch (e) {
            console.error("VAD 중지 오류:", e);
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
    }, [vadPause]);

    // 녹음 시작
    const startRecording = useCallback(async () => {
        if (vadLoading) {
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
                console.log("📩 WebSocket 메시지 수신:", event.data);
                try {
                    const message = JSON.parse(event.data);
                    console.log("파싱된 메시지:", message);
                    
                    switch (message.type) {
                        case 'partial_transcript':
                            console.log("임시 전사:", message.text);
                            setPartialText(message.text);
                            break;
                            
                        case 'final_transcript':
                            console.log("최종 전사:", message.text);
                            setTranscript(prev => {
                                const newText = prev ? prev + '\n' + message.text : message.text;
                                return newText;
                            });
                            setPartialText('');
                            break;
                            
                        case 'translation':
                            console.log("번역 결과:", message.translated_text);
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
                    console.error("원본 데이터:", event.data);
                }
            };

            // WebSocket 종료 핸들러
            ws.onclose = (event) => {
                console.log("🔴 WebSocket 연결 종료");
                console.log("Close code:", event.code);
                console.log("Close reason:", event.reason);
                console.log("Was clean:", event.wasClean);
                console.log("현재 녹음 상태:", isRecordingRef.current);
                
                // Close code 설명
                const closeCodeMessages = {
                    1000: "정상 종료",
                    1001: "서버 종료",
                    1006: "비정상 종료 (네트워크 오류 또는 서버 문제)",
                    1011: "서버 내부 오류",
                    1012: "서버 재시작",
                };
                console.log("종료 사유:", closeCodeMessages[event.code] || "알 수 없음");
                
                if (isRecordingRef.current) {
                    setIsRecording(false);
                    setTranscript(prev => prev + `\n[서버 연결 종료 - Code: ${event.code}, ${closeCodeMessages[event.code] || "알 수 없음"}]`);
                }
            };

            // WebSocket 에러 핸들러 추가
            ws.onerror = (error) => {
                console.error("WebSocket 실행 중 오류:", error);
            };

            // VAD 시작 - start 메서드 사용
            if (typeof vadStart === 'function') {
                vadStart();
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
    }, [vadLoading, vadStart, cleanupResources]);

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
        isRecording: isRecording || vadLoading,
        transcript,
        partialText,
        translation,
        startRecording,
        stopRecording,
        vadLoading: vadLoading,
    };
};

export default useRealtimeStream;