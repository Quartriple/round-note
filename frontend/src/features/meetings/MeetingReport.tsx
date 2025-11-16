import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { Button } from '@/shared/ui/button';
import { Download, FileBarChart, Calendar, Users, Target, CheckCircle2, Clock, TrendingUp } from 'lucide-react';
import type { Meeting } from '@/features/dashboard/Dashboard';

interface MeetingReportProps {
  meeting: Meeting;
}

export function MeetingReport({ meeting }: MeetingReportProps) {
  const generateReportData = () => {
    const totalItems = meeting.actionItems.length;
    const completedItems = meeting.actionItems.filter(a => a.completed).length;
    const pendingItems = totalItems - completedItems;
    const completionRate = totalItems > 0 ? Math.round((completedItems / totalItems) * 100) : 0;

    // Extract participants
    const participants = new Set<string>();
    meeting.actionItems.forEach(item => {
      if (item.assignee && item.assignee !== '미정') {
        participants.add(item.assignee);
      }
    });

    // Calculate items per person
    const itemsPerPerson = Array.from(participants).map(person => {
      const personItems = meeting.actionItems.filter(item => item.assignee === person);
      const completed = personItems.filter(item => item.completed).length;
      return {
        name: person,
        total: personItems.length,
        completed,
        pending: personItems.length - completed,
        completionRate: Math.round((completed / personItems.length) * 100),
      };
    });

    // Items with due dates
    const itemsWithDueDate = meeting.actionItems.filter(item => item.dueDate);
    const overdueTasks = itemsWithDueDate.filter(item => {
      if (!item.completed && item.dueDate) {
        return new Date(item.dueDate) < new Date();
      }
      return false;
    });

    return {
      totalItems,
      completedItems,
      pendingItems,
      completionRate,
      participants: Array.from(participants),
      itemsPerPerson,
      overdueTasks: overdueTasks.length,
      totalWithDueDate: itemsWithDueDate.length,
    };
  };

  const reportData = generateReportData();

  const handleDownloadReport = () => {
    const reportContent = `
==============================================
회의록 리포트
==============================================

회의 정보
--------------
제목: ${meeting.title}
날짜: ${meeting.date}
작성일: ${new Date(meeting.createdAt).toLocaleDateString('ko-KR')}

회의 요약
--------------
${meeting.summary}

핵심 지표
--------------
• 총 액션 아이템: ${reportData.totalItems}개
• 완료된 항목: ${reportData.completedItems}개
• 진행 중 항목: ${reportData.pendingItems}개
• 완료율: ${reportData.completionRate}%
• 참여자 수: ${reportData.participants.length}명
• 마감 지연 항목: ${reportData.overdueTasks}개

참여자별 현황
--------------
${reportData.itemsPerPerson.map(person => 
  `${person.name}: ${person.total}개 (완료 ${person.completed}, 진행 ${person.pending}, 완료율 ${person.completionRate}%)`
).join('\n')}

액션 아이템 상세
--------------
${meeting.actionItems.map((item, index) => `
${index + 1}. [${item.completed ? '완료' : '진행중'}] ${item.text}
   담당자: ${item.assignee}
   마감일: ${item.dueDate || '미정'}
`).join('\n')}

전체 회의 내용
--------------
${meeting.content}

==============================================
생성일시: ${new Date().toLocaleString('ko-KR')}
==============================================
    `;

    const blob = new Blob([reportContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `회의리포트_${meeting.title}_${meeting.date}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileBarChart className="w-6 h-6 text-blue-600" />
          <h3 className="text-blue-600">회의 리포트</h3>
        </div>
        <Button onClick={handleDownloadReport} className="gap-2">
          <Download className="w-4 h-4" />
          리포트 다운로드
        </Button>
      </div>

      {/* Executive Summary */}
      <Card>
        <CardHeader>
          <CardTitle>요약</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <Target className="w-8 h-8 text-blue-600 mx-auto mb-2" />
              <p className="text-2xl">{reportData.totalItems}</p>
              <p className="text-sm text-gray-600">총 액션 아이템</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <CheckCircle2 className="w-8 h-8 text-green-600 mx-auto mb-2" />
              <p className="text-2xl">{reportData.completedItems}</p>
              <p className="text-sm text-gray-600">완료</p>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <Clock className="w-8 h-8 text-orange-600 mx-auto mb-2" />
              <p className="text-2xl">{reportData.pendingItems}</p>
              <p className="text-sm text-gray-600">진행 중</p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <TrendingUp className="w-8 h-8 text-purple-600 mx-auto mb-2" />
              <p className="text-2xl">{reportData.completionRate}%</p>
              <p className="text-sm text-gray-600">완료율</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Meeting Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            회의 정보
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex justify-between py-2 border-b">
            <span className="text-gray-600">회의 제목</span>
            <span>{meeting.title}</span>
          </div>
          <div className="flex justify-between py-2 border-b">
            <span className="text-gray-600">회의 날짜</span>
            <span>{meeting.date}</span>
          </div>
          <div className="flex justify-between py-2 border-b">
            <span className="text-gray-600">작성일</span>
            <span>{new Date(meeting.createdAt).toLocaleDateString('ko-KR')}</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-gray-600">최종 수정일</span>
            <span>{new Date(meeting.updatedAt).toLocaleDateString('ko-KR')}</span>
          </div>
        </CardContent>
      </Card>

      {/* Participants Performance */}
      {reportData.itemsPerPerson.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              참여자별 진행 현황
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {reportData.itemsPerPerson.map((person, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span>{person.name}</span>
                    <span className="text-sm text-gray-600">
                      {person.completed}/{person.total} ({person.completionRate}%)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all"
                      style={{ width: `${person.completionRate}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Overdue Tasks Warning */}
      {reportData.overdueTasks > 0 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-700">
              <Clock className="w-5 h-5" />
              마감 지연 알림
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-orange-800">
              현재 {reportData.overdueTasks}개의 액션 아이템이 마감일을 초과했습니다.
              담당자에게 확인이 필요합니다.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Progress Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            진행 상황
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm text-gray-600">완료</span>
                <span className="text-sm">{reportData.completedItems}개</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-green-500 h-3 rounded-full"
                  style={{
                    width: `${reportData.totalItems > 0 ? (reportData.completedItems / reportData.totalItems) * 100 : 0}%`,
                  }}
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm text-gray-600">진행 중</span>
                <span className="text-sm">{reportData.pendingItems}개</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-orange-500 h-3 rounded-full"
                  style={{
                    width: `${reportData.totalItems > 0 ? (reportData.pendingItems / reportData.totalItems) * 100 : 0}%`,
                  }}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Text */}
      <Card>
        <CardHeader>
          <CardTitle>회의 요약</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="whitespace-pre-wrap text-gray-700">{meeting.summary}</p>
        </CardContent>
      </Card>
    </div>
  );
}
