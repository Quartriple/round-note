// app/meetings/page.tsx
"use client";

import { MeetingListView } from "@/features/meetings/MeetingListView";
import type { Meeting } from "@/features/dashboard/Dashboard"; // Meeting 타입 불러오기

// 테스트용 더미 데이터 (mock.ts 없이 직접 선언)
const meetings: Meeting[] = [
  {
    id: "1",
    title: "예시 회의",
    date: "2023-11-17",
    summary: "회의 요약입니다.",
    content: "회의 전체 내용입니다.",
    actionItems: [
      { id: "a1", text: "할 일 1", completed: false, assignee: "홍길동", dueDate: "2023-11-20" },
      { id: "a2", text: "할 일 2", completed: true, assignee: "김철수", dueDate: "2023-11-22" },
    ],
    // Meeting 타입에 필수 필드가 있다면 여기에 추가
    createdAt: "2023-11-17T00:00:00Z",
    updatedAt: "2023-11-17T00:00:00Z",
  },
];

export default function MeetingsPage() {
  return (
    <main className="w-full flex justify-center">
      <div className="w-full max-w-[1400px] px-4">
        <MeetingListView
          meetings={meetings}
          onUpdateMeeting={(updated) => {
            // 추후 API 연동 시 PUT/PATCH 요청 처리
            console.log("업데이트된 회의:", updated);
          }}
          onDeleteMeeting={(id) => {
            // 추후 API 연동 시 DELETE 요청 처리
            console.log("삭제할 회의 ID:", id);
          }}
        />
      </div>
    </main>
  );
}