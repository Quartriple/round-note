"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Login } from "@/features/auth/Login";
import { useEffect } from "react";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    // Google OAuth 콜백에서 토큰을 받았는지 확인
    const token = searchParams.get('token');
    if (token) {
      localStorage.setItem('access_token', token);
      localStorage.setItem("roundnote-loggedin", "true");
      alert("Google 로그인에 성공하였습니다.");
      router.push("/main");
    }
  }, [searchParams, router]);

  return (
    <Login
      onLogin={() => {
        // 로그인 성공 시 localStorage에 상태 저장
        localStorage.setItem("roundnote-loggedin", "true");
        alert("로그인에 성공하였습니다.");
        router.push("/main"); // 메인 페이지로 이동
      }}
      onShowRegister={() => {
        router.push("/register"); // 회원가입 페이지로 이동
      }}
    />
  );
}