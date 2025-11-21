import { useState } from 'react';
import { MeetingInfoInput } from '@/features/meetings/MeetingInfoInput';
import { MeetingContentInput } from './MeetingContentInput';
import type { Meeting } from '@/features/dashboard/Dashboard';
import { createMeeting, endMeeting, type MeetingResponse } from '@/features/meetings/meetingsService';
import { toast } from 'sonner';

interface MeetingStartProps {
  meetings: Meeting[];
  onAddMeeting: (meeting: Meeting) => void;
}

export function MeetingStart({ meetings, onAddMeeting }: MeetingStartProps) {
  const [currentStep, setCurrentStep] = useState<'transcribe' | 'info'>('transcribe');
  const [transcribedContent, setTranscribedContent] = useState('');
  const [aiAnalysis, setAiAnalysis] = useState<any>(null);
  const [createdMeetingId, setCreatedMeetingId] = useState<string | null>(null);

  // 회의 전사 완료 시
  const handleContentComplete = (content: string, analysis?: any) => {
    setTranscribedContent(content);
    setAiAnalysis(analysis);
    setCurrentStep('info');
  };

  // 정보 입력 완료 시 - 최종 저장
  const handleInfoComplete = async (info: { title: string; date: string; purpose: string; participants: string[] }) => {
    // 1. 백엔드에 회의 생성 요청
    toast.info('회의를 저장하는 중...');
    
    let meetingData;
    try {
      meetingData = await createMeeting({
        title: info.title,
        purpose: info.purpose,
        is_realtime: true,
      });

      // 2. 생성된 회의 ID 저장
      setCreatedMeetingId(meetingData.meeting_id);
    } catch (createError) {
      console.error('[MeetingStart] Failed to create meeting:', createError);
      toast.error('회의 생성에 실패했습니다.');
      return;
    }

    // 3. 오디오 파일 업로드
    if (aiAnalysis?.audioBlob) {
      try {
        const formData = new FormData();
        formData.append('file', aiAnalysis.audioBlob, `${meetingData.meeting_id}.wav`);
        
        const token = localStorage.getItem('access_token');
        const uploadResponse = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/meetings/${meetingData.meeting_id}/audio`,
          {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
            },
            body: formData,
          }
        );
        
        if (uploadResponse.ok) {
          const uploadResult = await uploadResponse.json();
          console.log('[MeetingStart] Audio uploaded:', uploadResult);
          toast.success('오디오 파일이 업로드되었습니다.');
          await new Promise(resolve => setTimeout(resolve, 1000));
        } else {
          console.error('Audio upload failed:', await uploadResponse.text());
          toast.warning('오디오 파일 업로드에 실패했습니다.');
        }
      } catch (uploadError) {
        console.error('[MeetingStart] Audio upload error:', uploadError);
        toast.warning('오디오 파일 업로드 중 오류가 발생했습니다.');
      }
    }

    // 4. 회의 종료 + LLM 처리를 위한 헬퍼 함수들
    const extractActionItems = (text: string) => {
      const lines = text.split('\n');
      const actionItems = [];
      
      // 로컬스토리지에서 키워드 설정 가져오기
      const keywordSettings = localStorage.getItem('roundnote-keyword-settings');
      let actionKeywords = ['액션', '할일', '과제', '담당', '진행', '검토', '확인', '준비', '작성', '제출'];
      
      if (keywordSettings) {
        try {
          const settings = JSON.parse(keywordSettings);
          if (settings.actionKeywords && settings.actionKeywords.length > 0) {
            actionKeywords = settings.actionKeywords;
          }
        } catch (error) {
          console.error('Failed to load keyword settings:', error);
        }
      }
      
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

    // 5. 백엔드 API 호출: 회의 종료 + LLM 요약/액션아이템 자동 생성
    const token = localStorage.getItem('access_token');
    let summary = '';
    let actionItems: any[] = [];
    let audioUrl = '';    try {
      const endResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/meetings/${meetingData.meeting_id}/end`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            status: 'COMPLETED',
            ended_at: new Date().toISOString(),
            content: transcribedContent,
            audio_url: `./audio_storage/${meetingData.meeting_id}.wav`
          }),
        }
      );
      
      if (endResponse.ok) {
        const endResult = await endResponse.json();
        console.log('[MeetingStart] End meeting response:', endResult);
        
        // 백엔드에서 생성한 요약과 액션 아이템 사용
        summary = endResult.summary || '';
        audioUrl = endResult.audio_url || `./audio_storage/${meetingData.meeting_id}.wav`;
        
        // 액션 아이템 변환
        if (endResult.action_items && Array.isArray(endResult.action_items)) {
          actionItems = endResult.action_items.map((item: any, index: number) => ({
            id: `${Date.now()}-${index}`,
            text: item.task || '',
            assignee: item.assignee || '미정',
            dueDate: item.deadline || '',
            completed: false,
            priority: 'medium'
          }));
        }
        
        console.log('[MeetingStart] Using backend-generated summary and action items');
      } else {
        console.warn('[MeetingStart] Failed to end meeting on backend, using fallback');
        throw new Error('Failed to end meeting');
      }
    } catch (error) {
      console.error('[MeetingStart] Error calling end meeting API:', error);
      
      // Fallback: AI 분석 결과 또는 로컬 패턴 매칭 사용
      if (aiAnalysis) {
        summary = aiAnalysis.summary || generateSummary(transcribedContent);
        
        if (aiAnalysis.actionItems && Array.isArray(aiAnalysis.actionItems)) {
          actionItems = aiAnalysis.actionItems.map((item: any, index: number) => ({
            id: `${Date.now()}-${index}`,
            text: item.task || item.text || '',
            assignee: item.assignee || '미정',
            dueDate: item.dueDate || '',
            completed: false,
            priority: item.priority
          }));
        } else {
          actionItems = extractActionItems(transcribedContent);
        }
      } else {
        summary = generateSummary(transcribedContent);
        actionItems = extractActionItems(transcribedContent);
      }
      
      // 회의 정보 조회 시도
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/meetings/${meetingData.meeting_id}`,
          {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          }
        );
        
        if (response.ok) {
          const meetingFromBackend = await response.json();
          audioUrl = meetingFromBackend.audio_url || meetingFromBackend.location || `./audio_storage/${meetingData.meeting_id}.wav`;
          console.log('[MeetingStart] Fetched audio URL from backend:', audioUrl);
        } else {
          console.warn('[MeetingStart] Failed to fetch meeting from backend');
          audioUrl = `./audio_storage/${meetingData.meeting_id}.wav`;
        }
      } catch (fetchError) {
        console.error('[MeetingStart] Error fetching meeting:', fetchError);
        audioUrl = `./audio_storage/${meetingData.meeting_id}.wav`;
      }
    }
    
    const now = new Date().toISOString();
    
    const newMeeting: Meeting = {
      id: meetingData.meeting_id, // 백엔드에서 받은 ID 사용
      title: info.title,
      date: info.date,
      content: transcribedContent,
      summary,
      actionItems,
      createdAt: meetingData.start_dt || now,
      updatedAt: now,
      participants: info.participants,
      keyDecisions: aiAnalysis?.keyDecisions || [],
      nextSteps: aiAnalysis?.nextSteps || [],
      audioUrl: audioUrl // 백엔드에서 확인된 실제 경로 사용
    };
    
    console.log('[MeetingStart] New meeting object:', newMeeting);
    onAddMeeting(newMeeting);
    toast.success('회의가 성공적으로 저장되었습니다!');
  };

  const handleBack = () => {
    setCurrentStep('transcribe');
  };

  // 1단계: 회의 시작 (전사)
  if (currentStep === 'transcribe') {
    return (
      <MeetingContentInput 
        meetingInfo={{
          title: '',
          date: new Date().toISOString().split('T')[0],
          purpose: '',
          participants: ''
        }}
        onComplete={handleContentComplete}
        onBack={() => {}} // 뒤로가기 없음
      />
    );
  }

  // 2단계: 정보 입력 (제목, 목적, 참석자 등)
  // AI 분석 결과를 바탕으로 초기값 설정
  const generateDefaultTitle = () => {
    // 내용이 없으면 날짜 기반 디폴트 제목
    if (!transcribedContent.trim()) {
      const now = new Date();
      const dateStr = now.toISOString().split('T')[0]; // YYYY-MM-DD
      const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
      const count = meetings.filter(m => m.date === dateStr).length + 1;
      return `${dateStr} ${timeStr} 회의(${count})`;
    }
    
    // AI 분석 결과에서 제목 추출
    if (aiAnalysis?.title) {
      return aiAnalysis.title;
    }
    
    // 내용의 첫 줄을 제목으로 사용 (최대 50자)
    const firstLine = transcribedContent.split('\n')[0].trim();
    if (firstLine) {
      return firstLine.substring(0, 50) + (firstLine.length > 50 ? '...' : '');
    }
    
    // 기본 제목
    const dateStr = new Date().toISOString().split('T')[0];
    const count = meetings.filter(m => m.date === dateStr).length + 1;
    return `${dateStr} 회의(${count})`;
  };

  const generateDefaultPurpose = () => {
    // AI 분석 결과에서 목적 추출
    if (aiAnalysis?.purpose) {
      return aiAnalysis.purpose;
    }
    
    // 요약의 일부를 목적으로 사용
    if (aiAnalysis?.summary) {
      const summaryFirstLine = aiAnalysis.summary.split('\n')[0].trim();
      return summaryFirstLine.substring(0, 100);
    }
    
    return '';
  };

  return (
    <div className="bg-white rounded-2xl p-8 shadow-sm border border-border w-[1100PX]  max-w-[1100px] mx-auto">
      <div className="mb-6">
        <h2 className="text-foreground mb-2">회의 정보 입력</h2>
        <p className="text-sm text-muted-foreground">
          회의 전사가 완료되었습니다. 회의 정보를 확인하고 수정해주세요.
        </p>
      </div>
      <MeetingInfoInput 
        initialInfo={{
          title: generateDefaultTitle(),
          date: new Date().toISOString().split('T')[0],
          purpose: generateDefaultPurpose(),
          participants: aiAnalysis?.participants?.join(', ') || ''
        }}
        meetings={meetings}
        onComplete={handleInfoComplete}
      />
    </div>
  );
}