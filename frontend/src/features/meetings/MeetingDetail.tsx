import { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { Button } from '@/shared/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs';
import { Badge } from '@/shared/ui/badge';
import { Checkbox } from '@/shared/ui/checkbox';
import { Input } from '@/shared/ui/input';
import { 
  FileText, 
  Brain, 
  Calendar, 
  User, 
  Clock, 
  CheckCircle2,
  ListChecks,
  Download,
  Trash2,
  ArrowLeft,
  MoreVertical,
  FileDown,
  ChevronDown,
  ChevronUp,
  Languages,
  Play,
  Pause,
  Volume2,
  Settings,
  MessageSquare,
  Mic
} from 'lucide-react';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '../../shared/ui/collapsible';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../shared/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../../shared/ui/dropdown-menu';
import { MeetingAnalysis } from '@/features/realtime/MeetingAnalysis';
import { ScrollToTop } from '@/features/utils/ScrollToTop';
import { exportToPDF } from '@/utils/exportPDF';
import { exportToWord } from '@/utils/exportWord';
import type { Meeting, ActionItem } from '@/features/dashboard/Dashboard';

interface MeetingDetailProps {
  meeting: Meeting;
  onUpdateMeeting: (meeting: Meeting) => void;
  onDeleteMeeting: (id: string) => void;
  onClose: () => void;
}

export function MeetingDetail({
  meeting,
  onUpdateMeeting,
  onDeleteMeeting,
  onClose,
}: MeetingDetailProps) {
  const [activeTab, setActiveTab] = useState('basic');

  // Refs for scroll navigation
  const summaryRef = useRef<HTMLDivElement>(null);
  const actionItemsRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLDivElement>(null);

  // Collapsible states
  const [summaryOpen, setSummaryOpen] = useState(true);
  const [actionItemsOpen, setActionItemsOpen] = useState(true);
  const [contentOpen, setContentOpen] = useState(true);
  const [audioOpen, setAudioOpen] = useState(true);

  // Translation states
  const [summaryLang, setSummaryLang] = useState('ko');
  const [contentLang, setContentLang] = useState('ko');
  const [translatedSummary, setTranslatedSummary] = useState('');
  const [translatedContent, setTranslatedContent] = useState('');
  const [isTranslating, setIsTranslating] = useState(false);

  // Audio states
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioSrc, setAudioSrc] = useState('');
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

  // Set audio src with token on mount
  useEffect(() => {
    if (meeting.audioUrl) {
      const token = localStorage.getItem('access_token');
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const fullAudioUrl = `${apiUrl}/api/v1/meetings/${meeting.id}/audio?token=${token}`;
      setAudioSrc(fullAudioUrl);
    }
  }, [meeting.id, meeting.audioUrl]);

  // Scroll to section function
  const scrollToSection = (ref: React.RefObject<HTMLDivElement | null>) => {
    if (ref.current) {
      // Open the section if it's closed
      if (ref === summaryRef && !summaryOpen) setSummaryOpen(true);
      if (ref === actionItemsRef && !actionItemsOpen) setActionItemsOpen(true);
      if (ref === contentRef && !contentOpen) setContentOpen(true);
      if (ref === audioRef && !audioOpen) setAudioOpen(true);
      
      // Wait for opening animation, then scroll
      setTimeout(() => {
        ref.current?.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start',
          inline: 'nearest'
        });
      }, 100);
    }
  };

  const handleToggleActionItem = (actionItemId: string) => {
    const updatedActionItems = meeting.actionItems.map(item =>
      item.id === actionItemId ? { ...item, completed: !item.completed } : item
    );

    onUpdateMeeting({ ...meeting, actionItems: updatedActionItems });
  };

  const handleUpdateActionItem = (actionItemId: string, field: keyof ActionItem, value: string) => {
    const updatedActionItems = meeting.actionItems.map(item =>
      item.id === actionItemId ? { ...item, [field]: value } : item
    );

    onUpdateMeeting({ ...meeting, actionItems: updatedActionItems });
  };

  const calculateProgress = () => {
    if (meeting.actionItems.length === 0) return 100;
    const completed = meeting.actionItems.filter(item => item.completed).length;
    return Math.round((completed / meeting.actionItems.length) * 100);
  };

  const handleExportPDF = () => {
    exportToPDF(meeting);
  };

  const handleExportWord = () => {
    exportToWord(meeting);
  };

  const handleDelete = async () => {
    if (confirm('정말로 이 회의록을 삭제하시겠습니까?')) {
      try {
        const token = localStorage.getItem('access_token');
        if (!token) {
          alert('로그인이 필요합니다.');
          return;
        }

        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/meetings/${meeting.id}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          onDeleteMeeting(meeting.id);
          onClose();
        } else {
          alert('회의록 삭제에 실패했습니다.');
        }
      } catch (error) {
        console.error('Failed to delete meeting:', error);
        alert('회의록 삭제 중 오류가 발생했습니다.');
      }
    }
  };

  const handleTranslate = async (text: string, targetLang: string, type: 'summary' | 'content') => {
    setIsTranslating(true);
    
    // Mock translation - 실제로는 번역 API를 호출해야 합니다
    // 예: Google Translate API, DeepL API 등
    try {
      // Placeholder: 실제 번역 API 호출이 필요합니다
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      if (type === 'summary') {
        setTranslatedSummary(`[${targetLang.toUpperCase()}로 번역됨]\n${text}`);
      } else {
        setTranslatedContent(`[${targetLang.toUpperCase()}로 번역됨]\n${text}`);
      }
    } catch (error) {
      console.error('Translation error:', error);
    } finally {
      setIsTranslating(false);
    }
  };

  const handleAudioPlayPause = () => {
    // Audio playback toggle logic
    if (audioPlayerRef.current) {
      if (isPlaying) {
        audioPlayerRef.current.pause();
      } else {
        audioPlayerRef.current.play();
      }
    }
    setIsPlaying(!isPlaying);
  };

  const handleAudioDownload = async () => {
    if (!audioSrc) {
      console.error('[MeetingDetail] No audio source available');
      alert('오디오 파일을 사용할 수 없습니다.');
      return;
    }
    
    try {
      console.log('[MeetingDetail] Downloading from:', audioSrc);
      const response = await fetch(audioSrc);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const blob = await response.blob();
      console.log('[MeetingDetail] Downloaded blob:', blob.size, 'bytes');
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${meeting.title}_audio.wav`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      console.log('[MeetingDetail] Download completed');
    } catch (error) {
      console.error('[MeetingDetail] Download failed:', error);
      alert(`오디오 파일 다운로드에 실패했습니다: ${error}`);
    }
  };

  useEffect(() => {
    const currentRef = audioPlayerRef.current;
    if (currentRef) {
      currentRef.addEventListener('play', () => setIsPlaying(true));
      currentRef.addEventListener('pause', () => setIsPlaying(false));
    }
    return () => {
      if (currentRef) {
        currentRef.removeEventListener('play', () => setIsPlaying(true));
        currentRef.removeEventListener('pause', () => setIsPlaying(false));
      }
    };
  }, []);

  return (
    <div className="w-[1100px] mx-auto px-4 space-y-4 md:space-y-6">
      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <Button variant="ghost" size="sm" onClick={onClose} className="gap-2 -ml-2">
            <ArrowLeft className="w-4 h-4" />
            <span className="hidden sm:inline">목록으로</span>
          </Button>
          
          {/* Desktop Actions */}
          <div className="hidden md:flex gap-2">
            <Button variant="outline" size="sm" onClick={handleExportPDF} className="gap-2">
              <Download className="w-4 h-4" />
              PDF
            </Button>
            <Button variant="outline" size="sm" onClick={handleExportWord} className="gap-2">
              <Download className="w-4 h-4" />
              Word
            </Button>
            <Button variant="destructive" size="sm" onClick={handleDelete} className="gap-2">
              <Trash2 className="w-4 h-4" />
              삭제
            </Button>
          </div>

          {/* Mobile Actions */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild className="md:hidden">
              <Button variant="outline" size="sm">
                <MoreVertical className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={handleExportPDF}>
                <Download className="w-4 h-4 mr-2" />
                PDF로 내보내기
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleExportWord}>
                <FileDown className="w-4 h-4 mr-2" />
                Word로 내보내기
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleDelete} className="text-red-600">
                <Trash2 className="w-4 h-4 mr-2" />
                회의록 삭제
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <h1 className="text-blue-600">{meeting.title}</h1>

        {/* Info Cards - Mobile Optimized */}
        <div className="grid grid-cols-3 gap-2 md:gap-4">
          <Card className="shadow-sm">
            <CardContent className="p-3 md:p-4">
              <div className="flex flex-col items-center text-center gap-1">
                <Calendar className="w-5 h-5 md:w-6 md:h-6 text-blue-500 mb-1" />
                <p className="text-xs text-gray-500">회의 날짜</p>
                <p className="text-xs md:text-sm mt-1">{meeting.date}</p>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-sm">
            <CardContent className="p-3 md:p-4">
              <div className="flex flex-col items-center text-center gap-1">
                <ListChecks className="w-5 h-5 md:w-6 md:h-6 text-green-500 mb-1" />
                <p className="text-xs text-gray-500">액션 아이템</p>
                <p className="text-xs md:text-sm mt-1">{meeting.actionItems.length}개</p>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-sm">
            <CardContent className="p-3 md:p-4">
              <div className="flex flex-col items-center text-center gap-1">
                <CheckCircle2 className="w-5 h-5 md:w-6 md:h-6 text-purple-500 mb-1" />
                <p className="text-xs text-gray-500">진행률</p>
                <p className="text-xs md:text-sm mt-1">{calculateProgress()}%</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="basic" className="gap-1 md:gap-2 text-sm md:text-base">
            <FileText className="w-4 h-4" />
            <span className="hidden sm:inline">기본 정보</span>
            <span className="sm:hidden">기본</span>
          </TabsTrigger>
          <TabsTrigger value="analysis" className="gap-1 md:gap-2 text-sm md:text-base">
            <Brain className="w-4 h-4" />
            <span className="hidden sm:inline">심층 분석</span>
            <span className="sm:hidden">분석</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="basic" className="space-y-4 md:space-y-6 mt-4 md:mt-6">
          {/* Quick Navigation Buttons */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-3">
            <Button
              variant="outline"
              onClick={() => scrollToSection(summaryRef)}
              className="gap-2 border-primary/30 hover:bg-primary/10 hover:border-primary"
            >
              <MessageSquare className="w-4 h-4" />
              <span className="text-sm">회의 요약</span>
            </Button>
            <Button
              variant="outline"
              onClick={() => scrollToSection(actionItemsRef)}
              className="gap-2 border-primary/30 hover:bg-primary/10 hover:border-primary"
            >
              <ListChecks className="w-4 h-4" />
              <span className="text-sm">액션 아이템</span>
            </Button>
            <Button
              variant="outline"
              onClick={() => scrollToSection(contentRef)}
              className="gap-2 border-primary/30 hover:bg-primary/10 hover:border-primary"
            >
              <FileText className="w-4 h-4" />
              <span className="text-sm">회의 원문</span>
            </Button>
            <Button
              variant="outline"
              onClick={() => scrollToSection(audioRef)}
              className="gap-2 border-primary/30 hover:bg-primary/10 hover:border-primary"
            >
              <Mic className="w-4 h-4" />
              <span className="text-sm">오디오 파일</span>
            </Button>
          </div>

          {/* Meeting Summary */}
          <div ref={summaryRef}>
            <Collapsible open={summaryOpen} onOpenChange={setSummaryOpen}>
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      회의 요약
                    </CardTitle>
                    <div className="flex items-center gap-2">
                      <Select
                        value={summaryLang}
                        onValueChange={(lang) => {
                          setSummaryLang(lang);
                          if (lang !== 'ko') {
                            handleTranslate(meeting.summary, lang, 'summary');
                          } else {
                            setTranslatedSummary('');
                          }
                        }}
                      >
                        <SelectTrigger className="w-[140px] h-8">
                          <Languages className="w-4 h-4 mr-1" />
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ko">한국어</SelectItem>
                          <SelectItem value="en">English</SelectItem>
                          <SelectItem value="ja">日本語</SelectItem>
                          <SelectItem value="zh">中文</SelectItem>
                        </SelectContent>
                      </Select>
                      <CollapsibleTrigger asChild>
                        <Button variant="ghost" size="sm">
                          {summaryOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </Button>
                      </CollapsibleTrigger>
                    </div>
                  </div>
                </CardHeader>
                <CollapsibleContent>
                  <CardContent>
                    {isTranslating && summaryLang !== 'ko' ? (
                      <div className="text-center py-4 text-gray-500">번역 중...</div>
                    ) : (
                      <div className="prose max-w-none">
                        <p className="whitespace-pre-wrap text-gray-700">
                          {summaryLang === 'ko' ? meeting.summary : translatedSummary || meeting.summary}
                        </p>
                      </div>
                    )}
                  </CardContent>
                </CollapsibleContent>
              </Card>
            </Collapsible>
          </div>

          {/* Action Items */}
          <div ref={actionItemsRef}>
            <Collapsible open={actionItemsOpen} onOpenChange={setActionItemsOpen}>
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      액션 아이템
                      <Badge variant="secondary">
                        {meeting.actionItems.filter(a => a.completed).length} / {meeting.actionItems.length} 완료
                      </Badge>
                    </CardTitle>
                    <div className="flex items-center gap-2">
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => setActiveTab('analysis')}
                        className="gap-2"
                      >
                        <Settings className="w-4 h-4" />
                        <span className="hidden sm:inline">설정</span>
                      </Button>
                      <CollapsibleTrigger asChild>
                        <Button variant="ghost" size="sm">
                          {actionItemsOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </Button>
                      </CollapsibleTrigger>
                    </div>
                  </div>
                </CardHeader>
                <CollapsibleContent>
                  <CardContent>
                    {meeting.actionItems.length === 0 ? (
                      <p className="text-gray-500 text-center py-8">액션 아이템이 없습니다</p>
                    ) : (
                      <div className="space-y-3">
                        {meeting.actionItems.map((item) => (
                          <div
                            key={item.id}
                            className={`p-3 md:p-4 border rounded-lg ${
                              item.completed ? 'bg-gray-50 border-gray-200' : 'bg-white border-gray-300'
                            }`}
                          >
                            <div className="flex items-start gap-2 md:gap-3 mb-3">
                              <Checkbox
                                checked={item.completed}
                                onCheckedChange={() => handleToggleActionItem(item.id)}
                                className="mt-0.5 md:mt-1"
                              />
                              <p className={`flex-1 text-sm md:text-base ${item.completed ? 'line-through text-gray-500' : 'text-gray-900'}`}>
                                {item.text}
                              </p>
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
                                {item.completed && (
                                  <Badge variant="secondary" className="bg-green-100 text-green-700 text-xs">
                                    완료
                                  </Badge>
                                )}
                              </div>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 ml-6 md:ml-8">
                              <div className="space-y-1">
                                <label className="text-xs text-gray-500 flex items-center gap-1">
                                  <User className="w-3 h-3" />
                                  담당자
                                </label>
                                <Input
                                  value={item.assignee}
                                  onChange={(e) => handleUpdateActionItem(item.id, 'assignee', e.target.value)}
                                  placeholder="담당자 이름"
                                  className="h-8 md:h-9 text-sm"
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
                                  className="h-8 md:h-9 text-sm"
                                />
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </CollapsibleContent>
              </Card>
            </Collapsible>
          </div>

          {/* AI Analysis Results */}
          {((meeting.participants?.length ?? 0) > 0 ||
            (meeting.keyDecisions?.length ?? 0) > 0 ||
            (meeting.nextSteps?.length ?? 0) > 0) && (
            <Card className="bg-gradient-to-br from-blue-50 to-purple-50 border-blue-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="w-5 h-5 text-blue-600" />
                  AI 분석 결과
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {(meeting.participants?.length ?? 0)> 0 && (
                  <div>
                    <h4 className="flex items-center gap-2 mb-2">
                      <User className="w-4 h-4 text-purple-600" />
                      참석자
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {meeting.participants?.map((participant, index) => (
                        <Badge key={index} variant="secondary" className="bg-white">
                          {participant}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {(meeting.keyDecisions?.length ?? 0)> 0 && (
                  <div>
                    <h4 className="flex items-center gap-2 mb-2">
                      <CheckCircle2 className="w-4 h-4 text-green-600" />
                      주요 결정사항
                    </h4>
                    <ul className="space-y-2">
                      {meeting.keyDecisions?.map((decision, index) => (
                        <li key={index} className="flex items-start gap-2 text-sm">
                          <span className="text-green-600 shrink-0">•</span>
                          <span className="text-gray-700">{decision}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {(meeting.nextSteps?.length ?? 0)> 0 && (
                  <div>
                    <h4 className="flex items-center gap-2 mb-2">
                      <ListChecks className="w-4 h-4 text-blue-600" />
                      다음 단계
                    </h4>
                    <ul className="space-y-2">
                      {meeting.nextSteps?.map((step, index) => (
                        <li key={index} className="flex items-start gap-2 text-sm">
                          <span className="text-blue-600 shrink-0">{index + 1}.</span>
                          <span className="text-gray-700">{step}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Full Content */}
          <div ref={contentRef}>
            <Collapsible open={contentOpen} onOpenChange={setContentOpen}>
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      회의 원문
                    </CardTitle>
                    <div className="flex items-center gap-2">
                      <Select
                        value={contentLang}
                        onValueChange={(lang) => {
                          setContentLang(lang);
                          if (lang !== 'ko') {
                            handleTranslate(meeting.content, lang, 'content');
                          } else {
                            setTranslatedContent('');
                          }
                        }}
                      >
                        <SelectTrigger className="w-[140px] h-8">
                          <Languages className="w-4 h-4 mr-1" />
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ko">한국어</SelectItem>
                          <SelectItem value="en">English</SelectItem>
                          <SelectItem value="ja">日本語</SelectItem>
                          <SelectItem value="zh">中文</SelectItem>
                        </SelectContent>
                      </Select>
                      <CollapsibleTrigger asChild>
                        <Button variant="ghost" size="sm">
                          {contentOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </Button>
                      </CollapsibleTrigger>
                    </div>
                  </div>
                </CardHeader>
                <CollapsibleContent>
                  <CardContent>
                    {isTranslating && contentLang !== 'ko' ? (
                      <div className="text-center py-4 text-gray-500">번역 중...</div>
                    ) : (
                      <div className="bg-gray-50 rounded-lg p-4 max-h-[500px] overflow-y-auto">
                        <p className="whitespace-pre-wrap text-gray-700">
                          {contentLang === 'ko' ? meeting.content : translatedContent || meeting.content}
                        </p>
                      </div>
                    )}
                  </CardContent>
                </CollapsibleContent>
              </Card>
            </Collapsible>
          </div>

          {/* Audio File Section */}
          <div ref={audioRef}>
            <Collapsible open={audioOpen} onOpenChange={setAudioOpen}>
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <Volume2 className="w-5 h-5 text-purple-600" />
                      원본 오디오 파일
                    </CardTitle>
                    <CollapsibleTrigger asChild>
                      <Button variant="ghost" size="sm">
                        {audioOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </Button>
                    </CollapsibleTrigger>
                  </div>
                </CardHeader>
                <CollapsibleContent>
                  <CardContent>
                    {meeting.audioUrl && meeting.audioUrl.trim() !== '' ? (
                      <div className="space-y-4">
                      <div className="bg-gray-50 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center gap-3">
                            <div className="text-sm text-gray-600">
                              <span className="font-medium">{meeting.title}</span> 녹음 파일
                            </div>
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={handleAudioDownload}
                            className="gap-2"
                          >
                            <Download className="w-4 h-4" />
                            다운로드
                          </Button>
                        </div>
                        <audio
                          ref={audioPlayerRef}
                          src={audioSrc}
                          controls
                          className="w-full"
                          onError={(e) => console.error('[MeetingDetail] Audio load error:', e)}
                        />
                      </div>
                      <p className="text-xs text-gray-500">
                        * 회의 중 녹음된 원본 오디오 파일입니다. 재생 또는 다운로드하여 다시 들을 수 있습니다.
                      </p>
                    </div>
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        <Volume2 className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                        <p>녹음된 오디오 파일이 없습니다</p>
                        <p className="text-xs mt-1">회의 시작 시 음성 녹음을 활성화하면 오디오 파일이 저장됩니다.</p>
                      </div>
                    )}
                  </CardContent>
                </CollapsibleContent>
              </Card>
            </Collapsible>
          </div>
        </TabsContent>

        <TabsContent value="analysis" className="mt-6">
          <MeetingAnalysis meeting={meeting} onUpdateMeeting={onUpdateMeeting} />
        </TabsContent>
      </Tabs>
      
      <ScrollToTop />
    </div>
  );
}