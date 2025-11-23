import { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { Send, Bot, User as UserIcon, RefreshCw, AlertCircle } from 'lucide-react';
import type { Meeting } from '@/features/dashboard/Dashboard';
import { chatWithMeeting, type ChatMessage as ApiChatMessage } from '@/features/meetings/reportsService';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isError?: boolean;
}

interface MeetingChatbotLLMProps {
  meeting: Meeting;
  /** 백엔드 API 사용 여부 (false면 로컬 로직 사용) */
  useBackendAPI?: boolean;
}

export function MeetingChatbotLLM({ meeting, useBackendAPI = true }: MeetingChatbotLLMProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: `안녕하세요! "${meeting.title}" 회의록에 대해 질문해주세요. 회의 내용을 기반으로 AI가 답변해드립니다.`,
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [connectionError, setConnectionError] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 메시지 히스토리를 API 형식으로 변환
  const getApiHistory = (): ApiChatMessage[] => {
    return messages
      .filter(m => m.id !== '1') // 초기 인사말 제외
      .map(m => ({
        role: m.role,
        content: m.content,
      }));
  };

  // 로컬 폴백 응답 생성 (API 연결 실패 시)
  const generateLocalResponse = (question: string): string => {
    const q = question.toLowerCase();

    if (q.includes('요약') || q.includes('정리')) {
      return `회의 요약:\n${meeting.summary}\n\n주요 액션 아이템은 ${meeting.actionItems.length}개이며, 그 중 ${meeting.actionItems.filter(a => a.completed).length}개가 완료되었습니다.`;
    }

    if (q.includes('액션') || q.includes('할일') || q.includes('과제')) {
      if (meeting.actionItems.length === 0) {
        return '현재 등록된 액션 아이템이 없습니다.';
      }
      const actionList = meeting.actionItems
        .map((item, index) => {
          const status = item.completed ? '✓ 완료' : '○ 진행중';
          const assignee = item.assignee || '미정';
          const dueDate = item.dueDate ? ` (마감: ${item.dueDate})` : '';
          return `${index + 1}. [${status}] ${item.text} - 담당: ${assignee}${dueDate}`;
        })
        .join('\n');
      return `총 ${meeting.actionItems.length}개의 액션 아이템이 있습니다:\n\n${actionList}`;
    }

    if (q.includes('참여자') || q.includes('참석') || q.includes('누가')) {
      const participants = new Set<string>();
      meeting.actionItems.forEach(item => {
        if (item.assignee && item.assignee !== '미정') {
          participants.add(item.assignee);
        }
      });
      
      if (participants.size === 0) {
        return '회의록에서 참여자 정보를 찾을 수 없습니다.';
      }
      return `확인된 참여자는 다음과 같습니다: ${Array.from(participants).join(', ')}`;
    }

    if (q.includes('날짜') || q.includes('언제') || q.includes('일정')) {
      return `이 회의는 ${meeting.date}에 진행되었습니다.`;
    }

    if (q.includes('내용') || q.includes('무엇') || q.includes('어떤')) {
      return `회의 내용:\n${meeting.content.substring(0, 500)}${meeting.content.length > 500 ? '...\n\n더 자세한 내용은 회의록 전문을 참고해주세요.' : ''}`;
    }

    return `죄송합니다. 현재 AI 서버와 연결되지 않아 기본 응답을 제공합니다.\n\n다음과 같은 질문을 시도해보세요:\n• "회의 요약해줘"\n• "액션 아이템 알려줘"\n• "참여자가 누구야?"`;
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = input.trim();
    setInput('');
    setIsTyping(true);
    setConnectionError(false);

    try {
      if (useBackendAPI) {
        // 백엔드 API 호출
        const response = await chatWithMeeting(
          meeting.id,
          currentInput,
          getApiHistory()
        );

        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.answer,
          timestamp: new Date(),
        };

        setMessages(prev => [...prev, assistantMessage]);
      } else {
        // 로컬 로직 사용
        await new Promise(resolve => setTimeout(resolve, 500));
        const response = generateLocalResponse(currentInput);
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response,
          timestamp: new Date(),
        };

        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (error) {
      console.error('Chat API error:', error);
      setConnectionError(true);
      
      // 에러 시 로컬 폴백
      const fallbackResponse = generateLocalResponse(currentInput);
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `⚠️ AI 서버 연결 실패. 기본 응답:\n\n${fallbackResponse}`,
        timestamp: new Date(),
        isError: true,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleRetry = () => {
    setConnectionError(false);
    // 마지막 사용자 메시지를 다시 전송
    const lastUserMessage = [...messages].reverse().find(m => m.role === 'user');
    if (lastUserMessage) {
      setInput(lastUserMessage.content);
    }
  };

  return (
    <Card className="h-[600px] flex flex-col">
      <CardHeader className="border-b">
        <CardTitle className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-blue-600" />
          AI 회의 챗봇
          {connectionError && (
            <span className="text-xs text-orange-500 flex items-center gap-1 ml-2">
              <AlertCircle className="w-3 h-3" />
              오프라인 모드
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col p-0">
        <div className="flex-1 p-4 overflow-y-auto">
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${
                  message.role === 'user' ? 'flex-row-reverse' : ''
                }`}
              >
                <div
                  className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    message.role === 'user'
                      ? 'bg-blue-600'
                      : message.isError
                      ? 'bg-orange-500'
                      : 'bg-purple-600'
                  }`}
                >
                  {message.role === 'user' ? (
                    <UserIcon className="w-4 h-4 text-white" />
                  ) : (
                    <Bot className="w-4 h-4 text-white" />
                  )}
                </div>
                <div
                  className={`flex-1 max-w-[80%] rounded-lg p-3 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : message.isError
                      ? 'bg-orange-50 text-gray-900 border border-orange-200'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <p className="whitespace-pre-wrap break-words">
                    {message.content}
                  </p>
                  <p
                    className={`text-xs mt-1 ${
                      message.role === 'user'
                        ? 'text-blue-100'
                        : 'text-gray-500'
                    }`}
                  >
                    {message.timestamp.toLocaleTimeString('ko-KR', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-purple-600">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-gray-100 rounded-lg p-3">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {connectionError && (
          <div className="px-4 py-2 bg-orange-50 border-t border-orange-200">
            <div className="flex items-center justify-between text-sm">
              <span className="text-orange-700">서버 연결 실패. 기본 응답을 사용 중입니다.</span>
              <Button variant="ghost" size="sm" onClick={handleRetry} className="text-orange-700">
                <RefreshCw className="w-4 h-4 mr-1" />
                재시도
              </Button>
            </div>
          </div>
        )}

        <div className="border-t p-4">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="회의에 대해 질문하세요..."
              className="flex-1"
            />
            <Button onClick={handleSend} disabled={!input.trim() || isTyping}>
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
