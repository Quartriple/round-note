import { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { Send, Bot, User as UserIcon } from 'lucide-react';
import type { Meeting } from '@/features/dashboard/Dashboard';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface MeetingChatbotProps {
  meeting: Meeting;
}

export function MeetingChatbot({ meeting }: MeetingChatbotProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: `안녕하세요! "${meeting.title}" 회의록에 대해 질문해주세요. 회의 내용, 액션 아이템, 참여자 등에 대한 정보를 제공해드릴 수 있습니다.`,
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const generateResponse = (question: string): string => {
    const q = question.toLowerCase();

    // Question about summary
    if (q.includes('요약') || q.includes('정리')) {
      return `회의 요약:\n${meeting.summary}\n\n주요 액션 아이템은 ${meeting.actionItems.length}개이며, 그 중 ${meeting.actionItems.filter(a => a.completed).length}개가 완료되었습니다.`;
    }

    // Question about action items
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

    // Question about participants
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

    // Question about date/time
    if (q.includes('날짜') || q.includes('언제') || q.includes('일정')) {
      return `이 회의는 ${meeting.date}에 진행되었습니다.`;
    }

    // Question about completed items
    if (q.includes('완료') || q.includes('끝난')) {
      const completed = meeting.actionItems.filter(a => a.completed);
      if (completed.length === 0) {
        return '아직 완료된 액션 아이템이 없습니다.';
      }
      const completedList = completed
        .map((item, index) => `${index + 1}. ${item.text} - ${item.assignee}`)
        .join('\n');
      return `완료된 액션 아이템 (${completed.length}개):\n\n${completedList}`;
    }

    // Question about pending items
    if (q.includes('진행') || q.includes('남은') || q.includes('미완료')) {
      const pending = meeting.actionItems.filter(a => !a.completed);
      if (pending.length === 0) {
        return '모든 액션 아이템이 완료되었습니다!';
      }
      const pendingList = pending
        .map((item, index) => {
          const assignee = item.assignee || '미정';
          const dueDate = item.dueDate ? ` (마감: ${item.dueDate})` : '';
          return `${index + 1}. ${item.text} - 담당: ${assignee}${dueDate}`;
        })
        .join('\n');
      return `진행 중인 액션 아이템 (${pending.length}개):\n\n${pendingList}`;
    }

    // Question about specific person
    const nameMatch = q.match(/([가-힣]{2,4})/);
    if (nameMatch) {
      const name = nameMatch[1];
      const personItems = meeting.actionItems.filter(item => 
        item.assignee === name
      );
      
      if (personItems.length > 0) {
        const itemsList = personItems
          .map((item, index) => {
            const status = item.completed ? '✓ 완료' : '○ 진행중';
            const dueDate = item.dueDate ? ` (마감: ${item.dueDate})` : '';
            return `${index + 1}. [${status}] ${item.text}${dueDate}`;
          })
          .join('\n');
        return `${name}님의 액션 아이템 (${personItems.length}개):\n\n${itemsList}`;
      }
    }

    // Question about content
    if (q.includes('내용') || q.includes('무엇') || q.includes('어떤')) {
      return `회의 내용:\n${meeting.content.substring(0, 500)}${meeting.content.length > 500 ? '...\n\n더 자세한 내용은 회의록 전문을 참고해주세요.' : ''}`;
    }

    // Default response
    return `질문에 대한 구체적인 답변을 찾지 못했습니다. 다음과 같은 질문을 보세요:\n\n• "회의 요약해줘"\n• "액션 아이템 알려줘"\n• "참여자가 누구야?"\n• "완료된 항목은?"\n• "진행 중인 항목은?"\n• "[이름]님의 할일은?"`;
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
    setInput('');
    setIsTyping(true);

    // Simulate thinking time
    setTimeout(() => {
      const response = generateResponse(input.trim());
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
      setIsTyping(false);
    }, 500);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Card className="h-[600px] flex flex-col">
      <CardHeader className="border-b">
        <CardTitle className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-blue-600" />
          회의 챗봇
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