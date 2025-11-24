import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { Textarea } from '@/shared/ui/textarea';
import { Badge } from '@/shared/ui/badge';
import { Checkbox } from '@/shared/ui/checkbox';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs';
import { 
  Brain, 
  MessageSquare, 
  FileBarChart, 
  TrendingUp, 
  Users, 
  Target, 
  AlertTriangle,
  Plus,
  Trash2,
  Calendar as CalendarIcon,
  ExternalLink,
  Clock,
  User
} from 'lucide-react';
import { MeetingReport } from '@/features/meetings/MeetingReport';
import { toast } from 'sonner';
import type { Meeting, ActionItem } from '@/features/dashboard/Dashboard';

interface MeetingAnalysisProps {
  meeting: Meeting;
  onUpdateMeeting?: (meeting: Meeting) => void;
}

export function MeetingAnalysis({ meeting, onUpdateMeeting }: MeetingAnalysisProps) {
  const [activeTab, setActiveTab] = useState('actionitems');
  const [newActionItem, setNewActionItem] = useState({ text: '', assignee: '', dueDate: '', priority: '중간' });
  const [editingId, setEditingId] = useState<string | null>(null);

  const handleAddActionItem = () => {
    if (!newActionItem.text.trim()) {
      toast.error('액션 아이템 내용을 입력해주세요.');
      return;
    }

    const actionItem: ActionItem = {
      id: Date.now().toString(),
      text: newActionItem.text,
      assignee: newActionItem.assignee || '미정',
      dueDate: newActionItem.dueDate,
      completed: false,
      priority: newActionItem.priority as '높음' | '중간' | '낮음'
    };

    if (onUpdateMeeting) {
      onUpdateMeeting({
        ...meeting,
        actionItems: [...meeting.actionItems, actionItem]
      });
    }

    setNewActionItem({ text: '', assignee: '', dueDate: '', priority: '중간' });
    toast.success('액션 아이템이 추가되었습니다.');
  };

  const handleUpdateActionItem = (id: string, field: keyof ActionItem, value: any) => {
    if (onUpdateMeeting) {
      const updatedItems = meeting.actionItems.map(item =>
        item.id === id ? { ...item, [field]: value } : item
      );
      onUpdateMeeting({
        ...meeting,
        actionItems: updatedItems
      });
    }
  };

  const handleDeleteActionItem = (id: string) => {
    if (confirm('이 액션 아이템을 삭제하시겠습니까?')) {
      if (onUpdateMeeting) {
        onUpdateMeeting({
          ...meeting,
          actionItems: meeting.actionItems.filter(item => item.id !== id)
        });
      }
      toast.success('액션 아이템이 삭제되었습니다.');
    }
  };

  const handleToggleComplete = (id: string) => {
    if (onUpdateMeeting) {
      const updatedItems = meeting.actionItems.map(item =>
        item.id === id ? { ...item, completed: !item.completed } : item
      );
      onUpdateMeeting({
        ...meeting,
        actionItems: updatedItems
      });
    }
  };

  const handleExportToGoogleCalendar = (item: ActionItem) => {
    const eventTitle = encodeURIComponent(item.text);
    const eventDate = item.dueDate ? item.dueDate.replace(/-/g, '') : '';
    const eventDetails = encodeURIComponent(`담당자: ${item.assignee}\n회의: ${meeting.title}`);
    
    const googleCalendarUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${eventTitle}&dates=${eventDate}/${eventDate}&details=${eventDetails}`;
    window.open(googleCalendarUrl, '_blank');
    toast.success('Google 캘린더로 이동합니다.');
  };


  const handleExportToJira = () => {
    toast.info('Jira 연동 기능은 준비 중입니다.');
  };

  // Generate comprehensive summary
  const generateComprehensiveSummary = () => {
    const lines = meeting.content.split('\n').filter(line => line.trim());
    
    // Extract key decisions
    const decisions = lines.filter(line => 
      /결정|확정|합의|승인/.test(line)
    );

    // Extract discussion points
    const discussions = lines.filter(line =>
      /논의|의견|검토|고려/.test(line)
    );

    // Extract risks or concerns
    const concerns = lines.filter(line =>
      /우려|위험|문제|이슈|리스크/.test(line)
    );

    return {
      decisions,
      discussions,
      concerns,
      totalParticipants: extractParticipants().length,
      totalActionItems: meeting.actionItems.length,
      completedActionItems: meeting.actionItems.filter(a => a.completed).length,
      pendingActionItems: meeting.actionItems.filter(a => !a.completed).length,
    };
  };

  const extractParticipants = () => {
    const participants = new Set<string>();
    meeting.actionItems.forEach(item => {
      if (item.assignee && item.assignee !== '미정') {
        participants.add(item.assignee);
      }
    });
    
    // Also extract from content
    const namePattern = /([가-힣]{2,4})(?:\s*님|\s*씨|\s*:|\s*담당)/g;
    let match;
    while ((match = namePattern.exec(meeting.content)) !== null) {
      participants.add(match[1]);
    }
    
    return Array.from(participants);
  };

  const calculatePriority = () => {
    const urgentKeywords = ['긴급', '급함', '중요', '우선', '즉시'];
    const urgentItems = meeting.actionItems.filter(item =>
      urgentKeywords.some(keyword => item.text.includes(keyword))
    );

    return {
      high: urgentItems.length,
      medium: meeting.actionItems.length - urgentItems.length,
      low: 0
    };
  };

  const summary = generateComprehensiveSummary();
  const participants = extractParticipants();
  const priority = calculatePriority();

  return (
    <div className="space-y-4 md:space-y-6">
      <div className="flex items-center gap-2">
        <Brain className="w-5 h-5 md:w-6 md:h-6 text-purple-600" />
        <h2 className="text-purple-600">액션 및 분석</h2>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="actionitems" className="gap-1 md:gap-2 text-xs md:text-sm">
            <Target className="w-3 h-3 md:w-4 md:h-4" />
            <span className="hidden sm:inline">액션 아이템 설정</span>
            <span className="sm:hidden">액션</span>
          </TabsTrigger>
          <TabsTrigger value="report" className="gap-1 md:gap-2 text-xs md:text-sm">
            <FileBarChart className="w-3 h-3 md:w-4 md:h-4" />
            리포트
          </TabsTrigger>
        </TabsList>

        <TabsContent value="actionitems" className="space-y-4 mt-4">
          {/* 액션 아이템 추가 */}
          <Card className="border-primary/20 bg-gradient-to-br from-blue-50 to-indigo-50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base md:text-lg">
                <Plus className="w-5 h-5 text-primary" />
                새 액션 아이템 추가
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2">
                <label className="text-sm font-medium">액션 아이템 내용</label>
                <Textarea
                  value={newActionItem.text}
                  onChange={(e) => setNewActionItem({ ...newActionItem, text: e.target.value })}
                  placeholder="예: 다음 주까지 마케팅 계획서 작성"
                  className="min-h-[80px]"
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="space-y-2">
                  <label className="text-sm font-medium flex items-center gap-1">
                    <User className="w-4 h-4" />
                    담당자
                  </label>
                  <Input
                    value={newActionItem.assignee}
                    onChange={(e) => setNewActionItem({ ...newActionItem, assignee: e.target.value })}
                    placeholder="담당자 이름"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    마감일
                  </label>
                  <Input
                    type="date"
                    value={newActionItem.dueDate}
                    onChange={(e) => setNewActionItem({ ...newActionItem, dueDate: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">우선순위</label>
                  <select
                    value={newActionItem.priority}
                    onChange={(e) => setNewActionItem({ ...newActionItem, priority: e.target.value })}
                    className="w-full h-10 px-3 rounded-md border border-slate-200 bg-white"
                  >
                    <option value="높음">높음</option>
                    <option value="중간">중간</option>
                    <option value="낮음">낮음</option>
                  </select>
                </div>
              </div>
              <Button onClick={handleAddActionItem} className="w-full gap-2">
                <Plus className="w-4 h-4" />
                액션 아이템 추가
              </Button>
            </CardContent>
          </Card>

          {/* 캘린더 및 협업 툴 연동 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base md:text-lg">
                <ExternalLink className="w-5 h-5 text-green-600" />
                업무 협업 툴 연동
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex justify-center">
                <Button variant="outline" className="w-[400px] gap-2 border-[#0052CC] text-[#0052CC] hover:bg-[#0052CC]/10" onClick={handleExportToJira}>
                  <ExternalLink className="w-4 h-4" />
                  Jira
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* 액션 아이템 목록 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base md:text-lg">
                <Target className="w-5 h-5 text-blue-600" />
                액션 아이템 목록
                <Badge variant="secondary">
                  {meeting.actionItems.filter(a => a.completed).length} / {meeting.actionItems.length} 완료
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {meeting.actionItems.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Target className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                  <p>아직 액션 아이템이 없습니다</p>
                  <p className="text-xs mt-1">위의 양식을 통해 액션 아이템을 추가하세요</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {meeting.actionItems.map((item) => (
                    <div
                      key={item.id}
                      className={`p-4 border rounded-lg ${
                        item.completed ? 'bg-gray-50 border-gray-200' : 'bg-white border-gray-300'
                      }`}
                    >
                      <div className="flex items-start gap-3 mb-3">
                        <Checkbox
                          checked={item.completed}
                          onCheckedChange={() => handleToggleComplete(item.id)}
                          className="mt-1"
                        />
                        {editingId === item.id ? (
                          <Textarea
                            value={item.text}
                            onChange={(e) => handleUpdateActionItem(item.id, 'text', e.target.value)}
                            className="flex-1 min-h-[60px]"
                            onBlur={() => setEditingId(null)}
                            autoFocus
                          />
                        ) : (
                          <p 
                            className={`flex-1 text-sm md:text-base cursor-pointer ${item.completed ? 'line-through text-gray-500' : 'text-gray-900'}`}
                            onClick={() => setEditingId(item.id)}
                          >
                            {item.text}
                          </p>
                        )}
                        <div className="flex gap-1 shrink-0">
                          {item.priority && (
                            <Badge 
                              variant="secondary" 
                              className={`text-xs ${
                                item.priority === '높음' ? 'bg-red-100 text-red-700' :
                                item.priority === '중간' ? 'bg-yellow-100 text-yellow-700' :
                                'bg-gray-100 text-gray-700'
                              }`}
                            >
                              {item.priority}
                            </Badge>
                          )}
                        </div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 ml-8">
                        <div className="space-y-1">
                          <label className="text-xs text-gray-500 flex items-center gap-1">
                            <User className="w-3 h-3" />
                            담당자
                          </label>
                          <Input
                            value={item.assignee}
                            onChange={(e) => handleUpdateActionItem(item.id, 'assignee', e.target.value)}
                            placeholder="담당자 이름"
                            className="h-8 text-sm"
                          />
                        </div>
                        <div className="space-y-1">
                          <label className="text-xs text-gray-500 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            마감일
                          </label>
                          <Input
                            type="date"
                            value={item.dueDate}
                            onChange={(e) => handleUpdateActionItem(item.id, 'dueDate', e.target.value)}
                            className="h-8 text-sm"
                          />
                        </div>
                        <div className="space-y-1">
                          <label className="text-xs text-gray-500">액션</label>
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleExportToGoogleCalendar(item)}
                              className="flex-1 gap-1 h-8 text-xs"
                            >
                              <CalendarIcon className="w-3 h-3" />
                              <span className="hidden md:inline">캘린더</span>
                            </Button>
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => handleDeleteActionItem(item.id)}
                              className="h-8 px-2"
                            >
                              <Trash2 className="w-3 h-3" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="summary" className="space-y-3 md:space-y-4 mt-4">
          {/* Key Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-4">
            <Card className="shadow-sm">
              <CardContent className="p-3 md:p-6 md:pt-6">
                <div className="flex flex-col md:flex-row items-center md:justify-between gap-2">
                  <div className="text-center md:text-left">
                    <p className="text-xs md:text-sm text-gray-600">참여자</p>
                    <p className="text-xl md:text-2xl mt-1">{summary.totalParticipants}</p>
                  </div>
                  <Users className="w-6 h-6 md:w-8 md:h-8 text-blue-500 opacity-50" />
                </div>
              </CardContent>
            </Card>

            <Card className="shadow-sm">
              <CardContent className="p-3 md:p-6 md:pt-6">
                <div className="flex flex-col md:flex-row items-center md:justify-between gap-2">
                  <div className="text-center md:text-left">
                    <p className="text-xs md:text-sm text-gray-600">액션 아이템</p>
                    <p className="text-xl md:text-2xl mt-1">{summary.totalActionItems}</p>
                  </div>
                  <Target className="w-6 h-6 md:w-8 md:h-8 text-green-500 opacity-50" />
                </div>
              </CardContent>
            </Card>

            <Card className="shadow-sm">
              <CardContent className="p-3 md:p-6 md:pt-6">
                <div className="flex flex-col md:flex-row items-center md:justify-between gap-2">
                  <div className="text-center md:text-left">
                    <p className="text-xs md:text-sm text-gray-600">완료</p>
                    <p className="text-xl md:text-2xl mt-1">{summary.completedActionItems}</p>
                  </div>
                  <TrendingUp className="w-6 h-6 md:w-8 md:h-8 text-purple-500 opacity-50" />
                </div>
              </CardContent>
            </Card>

            <Card className="shadow-sm">
              <CardContent className="p-3 md:p-6 md:pt-6">
                <div className="flex flex-col md:flex-row items-center md:justify-between gap-2">
                  <div className="text-center md:text-left">
                    <p className="text-xs md:text-sm text-gray-600">진행 중</p>
                    <p className="text-xl md:text-2xl mt-1">{summary.pendingActionItems}</p>
                  </div>
                  <AlertTriangle className="w-6 h-6 md:w-8 md:h-8 text-orange-500 opacity-50" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Participants */}
          <Card className="shadow-sm">
            <CardHeader className="pb-3 md:pb-6">
              <CardTitle className="flex items-center gap-2 text-base md:text-lg">
                <Users className="w-4 h-4 md:w-5 md:h-5 text-blue-600" />
                참여자 목록
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-1.5 md:gap-2">
                {participants.length > 0 ? (
                  participants.map((participant, index) => (
                    <div
                      key={index}
                      className="px-2 md:px-3 py-0.5 md:py-1 bg-blue-100 text-blue-700 rounded-full text-xs md:text-sm"
                    >
                      {participant}
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 text-xs md:text-sm">참여자 정보가 없습니다</p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Key Decisions */}
          {summary.decisions.length > 0 && (
            <Card className="shadow-sm">
              <CardHeader className="pb-3 md:pb-6">
                <CardTitle className="flex items-center gap-2 text-base md:text-lg">
                  <Target className="w-4 h-4 md:w-5 md:h-5 text-green-600" />
                  주요 결정사항
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {summary.decisions.slice(0, 5).map((decision, index) => (
                    <li key={index} className="flex gap-2">
                      <span className="text-green-600 mt-0.5 md:mt-1">•</span>
                      <span className="text-gray-700 text-sm md:text-base">{decision.trim()}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Discussion Points */}
          {summary.discussions.length > 0 && (
            <Card className="shadow-sm">
              <CardHeader className="pb-3 md:pb-6">
                <CardTitle className="flex items-center gap-2 text-base md:text-lg">
                  <MessageSquare className="w-4 h-4 md:w-5 md:h-5 text-purple-600" />
                  주요 논의사항
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {summary.discussions.slice(0, 5).map((discussion, index) => (
                    <li key={index} className="flex gap-2">
                      <span className="text-purple-600 mt-0.5 md:mt-1">•</span>
                      <span className="text-gray-700 text-sm md:text-base">{discussion.trim()}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Concerns */}
          {summary.concerns.length > 0 && (
            <Card className="shadow-sm">
              <CardHeader className="pb-3 md:pb-6">
                <CardTitle className="flex items-center gap-2 text-base md:text-lg">
                  <AlertTriangle className="w-4 h-4 md:w-5 md:h-5 text-orange-600" />
                  우려사항 및 리스크
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {summary.concerns.slice(0, 5).map((concern, index) => (
                    <li key={index} className="flex gap-2">
                      <span className="text-orange-600 mt-0.5 md:mt-1">•</span>
                      <span className="text-gray-700 text-sm md:text-base">{concern.trim()}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Action Items by Priority */}
          <Card className="shadow-sm">
            <CardHeader className="pb-3 md:pb-6">
              <CardTitle className="flex items-center gap-2 text-base md:text-lg">
                <Target className="w-4 h-4 md:w-5 md:h-5 text-blue-600" />
                액션 아이템 우선순위
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs md:text-sm text-gray-600 w-12">높음</span>
                  <div className="flex-1 mx-2 md:mx-4 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-red-500 h-2 rounded-full"
                      style={{ width: `${(priority.high / meeting.actionItems.length) * 100}%` }}
                    />
                  </div>
                  <span className="text-xs md:text-sm w-8 text-right">{priority.high}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs md:text-sm text-gray-600 w-12">중간</span>
                  <div className="flex-1 mx-2 md:mx-4 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-yellow-500 h-2 rounded-full"
                      style={{ width: `${(priority.medium / meeting.actionItems.length) * 100}%` }}
                    />
                  </div>
                  <span className="text-xs md:text-sm w-8 text-right">{priority.medium}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        

        <TabsContent value="report" className="mt-4">
          <MeetingReport meeting={meeting} showExports={false} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
