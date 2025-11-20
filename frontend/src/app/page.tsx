"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Page() {
  const router = useRouter();

  useEffect(() => {
    // JWT 토큰 확인
    const token = localStorage.getItem('access_token');
    
    if (token) {
      // 토큰이 있으면 메인 페이지로
      router.replace("/main");
    } else {
      // 토큰이 없으면 로그인 페이지로
      router.replace("/login");
    }
  }, [router]);

  // 리다이렉트 중에는 빈 화면 표시
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
        <p className="mt-4 text-muted-foreground">로딩 중...</p>
      </div>
    </div>
  );
}