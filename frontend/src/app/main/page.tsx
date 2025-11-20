"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Dashboard from "@/features/dashboard/Dashboard";

export default function MainPage() {
  const router = useRouter();

  useEffect(() => {
    // JWT 토큰 확인
    const token = localStorage.getItem('access_token');
    if (!token) {
      // 토큰이 없으면 로그인 페이지로
      router.replace("/login");
    }
  }, [router]);

  return <Dashboard />;
}