import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { Textarea } from '@/shared/ui/textarea';
import { Label } from '@/shared/ui/label';
import { Alert, AlertDescription } from '@/shared/ui/alert';
import { Sparkles, Calendar, Mic, MicOff, AlertCircle } from 'lucide-react';
import type { Meeting } from '@/features/dashboard/Dashboard';

interface MeetingInputProps {
  onAddMeeting: (meeting: Meeting) => void;
}

export function MeetingInput({ onAddMeeting }: MeetingInputProps) {
  const [title, setTitle] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [content, setContent] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(true);
  const [micPermissionDenied, setMicPermissionDenied] = useState(false);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    // Check for speech recognition support
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      setSpeechSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'ko-KR';

    recognition.onresult = (event: any) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript + ' ';
        } else {
          interimTranscript += transcript;
        }
      }

      if (finalTranscript) {
        setContent(prev => prev + finalTranscript);
      }
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      if (event.error === 'no-speech') {
        // Ignore no-speech errors
        return;
      }
      if (event.error === 'not-allowed') {
        setMicPermissionDenied(true);
        setSpeechSupported(false);
      }
      setIsRecording(false);
    };

    recognition.onend = () => {
      if (isRecording) {
        // Restart if we're still supposed to be recording
        recognition.start();
      }
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [isRecording]);

  const toggleRecording = async () => {
    if (!recognitionRef.current) return;

    if (isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
    } else {
      try {
        // Request microphone permission first
        await navigator.mediaDevices.getUserMedia({ audio: true });
        setMicPermissionDenied(false);
        recognitionRef.current.start();
        setIsRecording(true);
      } catch (error) {
        // Only log if it's not a permission denial (which is expected behavior)
        if (error instanceof Error && error.name !== 'NotAllowedError') {
          console.error('Microphone error:', error);
        }
        setMicPermissionDenied(true);
        setSpeechSupported(false);
      }
    }
  };

  const extractActionItems = (text: string) => {
    const lines = text.split('\n');
    const actionItems = [];
    const actionKeywords = ['액션', '할일', '과제', '담당', '진행', '검토', '확인', '준비', '작성', '제출'];
    
    for (const line of lines) {
      const trimmedLine = line.trim();
      if (trimmedLine.length > 5 && actionKeywords.some(keyword => trimmedLine.includes(keyword))) {
        const assigneeMatch = trimmedLine.match(/([가-힣]{2,4})\s*(?:님|씨|:|,)/);
        const assignee = assigneeMatch ? assigneeMatch[1] : '미정';
        
        actionItems.push({
          id: `${Date.now()}-${Math.random()}`,
          text: trimmedLine.replace(/^[-•*]\s*/, ''),
          assignee,
          dueDate: '',
          completed: false
        });
      }
    }
    
    return actionItems;
  };

  const generateSummary = (text: string) => {
    const lines = text.split('\n').filter(line => line.trim().length > 0);
    const summaryLines = [];
    
    const importantKeywords = ['결정', '합의', '중요', '주요', '핵심', '논의', '결론'];
    
    for (const line of lines) {
      if (importantKeywords.some(keyword => line.includes(keyword))) {
        summaryLines.push(line.trim().replace(/^[-•*]\s*/, ''));
      }
    }
    
    if (summaryLines.length === 0 && lines.length > 0) {
      summaryLines.push(...lines.slice(0, 3).map(l => l.trim().replace(/^[-•*]\s*/, '')));
    }
    
    return summaryLines.length > 0 
      ? summaryLines.join('\n') 
      : '회의 내용에서 주요 사항을 추출하지 못했습니다.';
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!title.trim() || !content.trim()) {
      alert('회의 제목과 내용을 모두 입력해주세요.');
      return;
    }

    if (isRecording) {
      toggleRecording();
    }

    setIsProcessing(true);
    
    setTimeout(() => {
      const summary = generateSummary(content);
      const actionItems = extractActionItems(content);
      const now = new Date().toISOString();
      
      const newMeeting: Meeting = {
        id: Date.now().toString(),
        title,
        date,
        content,
        summary,
        actionItems,
        createdAt: now,
        updatedAt: now
      };
      
      onAddMeeting(newMeeting);
      
      setTitle('');
      setContent('');
      setDate(new Date().toISOString().split('T')[0]);
      setIsProcessing(false);
    }, 800);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>새 회의록 작성</CardTitle>
        <CardDescription>
          실시간 음성 인식 또는 직접 입력으로 회의 내용을 기록하세요
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {!speechSupported && !micPermissionDenied && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                이 브라우저는 음성 인식을 지원하지 않습니다. Chrome 브라우저 사용을 권장합니다.
              </AlertDescription>
            </Alert>
          )}
          
          {micPermissionDenied && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                마이크 권한이 거부되었습니다. 브라우저 설정에서 마이크 권한을 허용해주세요.
                <br />
                <span className="text-xs mt-1 block">
                  Chrome: 주소창 왼쪽 자물쇠 아이콘 → 사이트 설정 → 마이크 권한 허용
                </span>
              </AlertDescription>
            </Alert>
          )}

          <div className="space-y-2">
            <Label htmlFor="title">회의 제목</Label>
            <Input
              id="title"
              placeholder="예: 2025년 1분기 마케팅 전략 회의"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="date" className="flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              회의 날짜
            </Label>
            <Input
              id="date"
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="content">회의 내용</Label>
              {speechSupported && !micPermissionDenied && (
                <Button
                  type="button"
                  variant={isRecording ? "destructive" : "outline"}
                  size="sm"
                  onClick={toggleRecording}
                  className="gap-2"
                >
                  {isRecording ? (
                    <>
                      <MicOff className="w-4 h-4" />
                      녹음 중지
                    </>
                  ) : (
                    <>
                      <Mic className="w-4 h-4" />
                      음성 입력
                    </>
                  )}
                </Button>
              )}
            </div>
            {isRecording && (
              <Alert className="bg-red-50 border-red-200">
                <Mic className="h-4 w-4 text-red-600" />
                <AlertDescription className="text-red-800">
                  음성 인식 중... 말씀하시면 자동으로 텍스트로 변환됩니다.
                </AlertDescription>
              </Alert>
            )}
            <Textarea
              id="content"
              placeholder="회의 내용을 자유롭게 입력하세요. 액션 아이템이나 중요 사항에는 '액션', '할일', '담당' 등의 키워드를 포함하면 더 정확하게 추출됩니다.

예시:
- 주요 논의사항: 신제품 출시 일정 확정
- 결정사항: 3월 15일 출시로 최종 결정
- 김민수 담당: 마케팅 자료 준비
- 이지은 담당: 홈페이지 업데이트 진행"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="min-h-[300px]"
            />
          </div>

          <Button 
            type="submit" 
            className="w-full gap-2"
            disabled={isProcessing}
          >
            <Sparkles className="w-4 h-4" />
            {isProcessing ? '분석 중...' : '회의록 생성'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}