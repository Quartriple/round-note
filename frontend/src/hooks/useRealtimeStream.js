import { useState, useRef, useCallback, useEffect } from 'react';

// WebSocket 설정 관련 전역 상수
const WS_URL = process.env.REACT_APP_API_URL ? 
    `ws${process.env.REACT_APP_API_URL.substring(4)}/api/v1/realtime/ws` : 
    'ws://localhost:8000/api/v1/realtime/ws';

// 오디오 설정 (Deepgram 요구사항에 맞춤)
const AUDIO_CONFIG = {
    sampleRate: 16000,
    channel: 1, // Web Audio API는 모노(1) 채널만 처리
    bufferSize: 4096,
};

const useRealtimeStream = () => {
    // 1. 상태 정의
    const [isRecording, setIsRecording] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [partialText, setPartialText] = useState('');
    const [translation, setTranslation] = useState('');

    // 2. Mutable 객체 참조 (리액트 렌더링 없이 값을 유지)
    const wsRef = useRef(null); // WebSocket 연결 객체
    const mediaStreamRef = useRef(null); // 마이크 스트림 객체
    const audioProcessorRef = useRef(null); // 오디오 노드(Node) 객체
    const audioContextRef = useRef(null); // AudioContext 객체


    // 이 함수는 모든 리소스(WebSocket, 마이크, 오디오 프로세서)를 정리합니다.
    // stopRecording과 startRecording의 catch 블록에서 재사용됩니다.
    const cleanupResources = useCallback(() => {
        // 1. WebSocket 연결 닫기
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
            console.log("WebSocket 리소스 정리됨.");
        }

        // 2. 마이크 스트림 해제
        if (mediaStreamRef.current) {
            mediaStreamRef.current.getTracks().forEach(track => {
                track.stop();
            });
            mediaStreamRef.current = null;
            console.log("마이크 스트림 리소스 정리됨.");
        }

        // 3. AudioWorklet/프로세서 노드 해제
        if (audioProcessorRef.current) {
            audioProcessorRef.current.disconnect();
            audioProcessorRef.current = null;
            console.log("오디오 프로세서 리소스 정리됨.");
        }

        // AudioContext는 모든 노드와 스트림이 해제된 후 닫는 것이 안전합니다.
        if (audioContextRef.current) {
            audioContextRef.current.close();
            audioContextRef.current = null;
            console.log("AudioContext 리소스 정리됨.");
        }
    }, []);

    // -----------------------------------------------------------
    // A. 마이크 접근 및 오디오 스트림 시작
    // -----------------------------------------------------------
    const startRecording = useCallback(async () => {
        if (isRecording) return;

        try {
            // 1. 마이크 접근 및 WebSocket 연결 (기존과 동일)
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: { 
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: AUDIO_CONFIG.sampleRate
                 } 
            });
            mediaStreamRef.current = stream;
            
            const ws = new WebSocket(WS_URL + "?translate=true");
            wsRef.current = ws;

            await new Promise((resolve, reject) => {
                ws.onopen = resolve;
                ws.onerror = reject;
            });
            
            // 2. AudioWorklet 환경 설정
            const audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: AUDIO_CONFIG.sampleRate,
            });
            audioContextRef.current = audioContext;
            
            // 3. [핵심] AudioWorklet Processor 파일 로드 (await 필요)
            await audioContext.audioWorklet.addModule('/mic-processor.js'); 
            
            // 4. 노드 생성: MediaStreamSource -> AudioWorkletNode
            const input = audioContext.createMediaStreamSource(stream);
            
            // AudioWorklet에 등록된 이름('mic-processor')으로 노드를 생성합니다.
            const processor = new AudioWorkletNode(audioContext, 'mic-processor');
            audioProcessorRef.current = processor;
            
            // 5. [핵심] AudioWorklet에서 데이터를 받아 WebSocket으로 중계하는 로직
            //    AudioWorklet은 별도의 스레드에서 처리된 데이터를 MessagePort를 통해 보냅니다.
            processor.port.onmessage = (event) => {
                const audioBuffer = event.data; // Worklet으로부터 받은 Int16Array.buffer
                
                // WebSocket이 열려있는지 확인 후 전송
                if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                    wsRef.current.send(audioBuffer);
                }
            };

            // 6. 오디오 파이프라인 연결: 마이크 -> 프로세서 -> 목적지(출력)
            // processor를 destination에 연결해야 브라우저가 활성 상태로 유지합니다.
            input.connect(processor);
            processor.connect(audioContext.destination);

            setIsRecording(true);
            setTranscript('🎙️ 실시간 전사를 시작합니다. (AudioWorklet 방식)');

        } catch (e) {
            console.error("마이크/WebSocket 연결 오류:", e);
            alert("마이크 접근 권한이 거부되었거나 WebSocket 연결에 실패했습니다.");
            cleanupResources();
            setIsRecording(false);
        }
    }, [isRecording, cleanupResources]);
    

    // -----------------------------------------------------------
    // B. 마이크 및 WebSocket 연결 중지
    // -----------------------------------------------------------
    const stopRecording = useCallback(() => {
        if (!isRecording) return;
        
        cleanupResources();

        // 4. 상태 초기화
        setIsRecording(false);
        setPartialText('');
        // 최종 전사 텍스트를 남겨두거나, '최종 요약 중...' 메시지를 표시할 수 있습니다.
        setTranscript(prev => prev + '\n[녹음 종료]');
        console.log("녹음 중지 완료.");

    }, [isRecording, cleanupResources]);

    // -----------------------------------------------------------
    // C. WebSocket 메시지 수신
    // -----------------------------------------------------------
    useEffect(() => {
        const ws = wsRef.current; // 현재 WebSocket 참조를 가져옵니다.

        if (ws) {
            // 1. 서버로부터 메시지를 수신했을 때 호출될 핸들러
            ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    
                    switch (message.type) {
                        case 'partial_transcript':
                            // 임시 전사 텍스트 (Deepgram 응답)
                            setPartialText(message.text);
                            break;
                            
                        case 'final_transcript':
                            // 최종 전사 텍스트 (Deepgram 응답)
                            // 최종 텍스트는 누적되어야 하므로 기존 transcript에 추가
                            setTranscript(prev => prev + '\n' + message.text);
                            setPartialText(''); // 임시 텍스트 초기화
                            break;
                            
                        case 'translation':
                            // 번역 결과 (LLM Service 응답)
                            setTranslation(message.translated_text);
                            // 참고: 실제 구현에서는 이 번역 결과를 최종 전사 옆에 붙이거나
                            // 별도의 리스트에 누적하는 로직이 필요합니다.
                            break;
                            
                        case 'error':
                            // 서버 측 오류 (FastAPI/Deepgram/OpenAI 오류)
                            console.error("Server Error:", message.message);
                            setPartialText(`[ERROR]: ${message.message}`);
                            break;
                            
                        // (추후 summary, action_items 등의 type도 여기서 처리)
                        
                        default:
                            console.warn("Unknown message type received:", message.type);
                    }
                } catch (e) {
                    console.error("WebSocket Message Parsing Error:", e);
                }
            };
            
            // 2. 연결 종료 시
            ws.onclose = () => {
                console.log("WebSocket 연결이 서버/클라이언트 측에서 닫혔습니다.");
                // isRecording이 True인 상태에서 연결이 끊기면 오류로 간주하고 상태 정리
                if (isRecording) {
                    stopRecording();
                    setTranscript(prev => prev + '\n[서버 연결 오류로 종료]');
                }
            };
        }
        
        // 3. 클린업(Cleanup) 함수: 컴포넌트가 언마운트될 때 실행
        // (주의) 이 useEffect는 wsRef.current가 바뀔 때마다 실행되므로, 
        // 기존의 onmessage 핸들러를 해제하는 클린업이 필요합니다.
        return () => {
            if (ws) {
                // 핸들러 중복 등록 방지
                ws.onmessage = null; 
                ws.onclose = null;
            }
        };
    }, [stopRecording, wsRef.current]);


    // 3. 외부에 노출할 상태와 함수를 반환합니다.
    return {
        isRecording,
        transcript,
        partialText,
        translation,
        startRecording,
        stopRecording
    };
};

export default useRealtimeStream;