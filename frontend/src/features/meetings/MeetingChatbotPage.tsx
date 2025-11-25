import { useState, useMemo, useEffect } from 'react';
import { Card, CardContent } from '@/shared/ui/card';
import { Input } from '@/shared/ui/input';
import { Search, Calendar, Clock } from 'lucide-react';
import type { Meeting } from '@/features/dashboard/Dashboard';
import { MeetingChatbotLLM } from '@/features/realtime/MeetingChatbotLLM';

interface MeetingChatbotPageProps {
    meetings: Meeting[];
}

export function MeetingChatbotPage({ meetings }: MeetingChatbotPageProps) {
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);

    // 검색어에 따른 회의 필터링
    const filteredMeetings = useMemo(() => {
        if (!searchQuery.trim()) {
            // 검색어가 없으면 최근 5개 회의 반환
            return meetings.slice(0, 5);
        }

        // 검색어로 필터링
        const query = searchQuery.toLowerCase();
        return meetings
            .filter(
                (meeting) =>
                    meeting.title.toLowerCase().includes(query) ||
                    meeting.content.toLowerCase().includes(query) ||
                    meeting.summary.toLowerCase().includes(query)
            )
            .slice(0, 5); // 최대 5개만 표시
    }, [meetings, searchQuery]);

    // 회의 목록이 변경되면 선택된 회의가 여전히 유효한지 확인
    useEffect(() => {
        if (selectedMeeting && !filteredMeetings.find(m => m.id === selectedMeeting.id)) {
            setSelectedMeeting(null);
        }
    }, [filteredMeetings, selectedMeeting]);

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
        });
    };

    const formatTime = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    return (
        <div className="h-[calc(100vh-2rem)] flex flex-col gap-4 p-4">
            {/* 검색창 */}
            <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                <Input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="회의 제목 또는 내용으로 검색..."
                    className="pl-10 h-12 text-base"
                />
            </div>

            {/* 최근 회의 카드 (가로 배치) */}
            <div className="flex gap-3 overflow-x-auto pb-2 min-w-[1100px]">
                {filteredMeetings.length === 0 ? (
                    <div className="w-[1100px] text-center py-8 text-muted-foreground">
                        {searchQuery ? '검색 결과가 없습니다.' : '회의 내역이 없습니다.'}
                    </div>
                ) : (
                    filteredMeetings.map((meeting) => (
                        <Card
                            key={meeting.id}
                            className={`flex-shrink-0 w-50 cursor-pointer transition-all hover:shadow-lg ${selectedMeeting?.id === meeting.id
                                ? 'border-2 border-primary bg-primary/5'
                                : 'border hover:border-primary/50'
                                }`}
                            onClick={() => setSelectedMeeting(meeting)}
                        >
                            <CardContent className="p-4">
                                <h3 className="font-semibold text-sm mb-2 line-clamp-2" title={meeting.title}>
                                    {meeting.title}
                                </h3>
                                <div className="space-y-1 text-xs text-muted-foreground">
                                    <div className="flex items-center gap-1">
                                        <Calendar className="w-3 h-3" />
                                        <span>{formatDate(meeting.date)}</span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <Clock className="w-3 h-3" />
                                        <span>{formatTime(meeting.createdAt)}</span>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))
                )}
            </div>

            {/* 챗봇 영역 */}
            <div className="flex-1 min-h-0">
                {selectedMeeting ? (
                    <MeetingChatbotLLM meeting={selectedMeeting} useBackendAPI={true} />
                ) : (
                    <Card className="h-full flex items-center justify-center">
                        <CardContent className="text-center py-16">
                            <div className="text-muted-foreground space-y-2">
                                <p className="text-lg font-medium">회의를 선택해주세요</p>
                                <p className="text-sm">
                                    위의 회의 목록에서 대화하고 싶은 회의를 선택하세요
                                </p>
                            </div>
                        </CardContent>
                    </Card>
                )}
            </div>
        </div>
    );
}
