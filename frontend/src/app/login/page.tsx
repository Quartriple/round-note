"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Login } from "@/features/auth/Login";
import { useEffect, Suspense } from "react";

// useSearchParams를 사용하는 컴포넌트를 분리
function LoginHandler({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    // 이미 로그인되어 있는지 확인
    const existingToken = localStorage.getItem('access_token');
    if (existingToken) {
      router.replace("/main");
      return;
    }

    // Google OAuth 콜백에서 토큰을 받았는지 확인
    const token = searchParams.get('token');
    if (token) {
      localStorage.setItem('access_token', token);
      alert("Google 로그인에 성공하였습니다.");
      router.push("/main");
    }
  }, [searchParams, router]);

  return <>{children}</>;
}

export default function LoginPage() {
  const router = useRouter();

  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen">Loading...</div>}>
      <LoginHandler>
        <Login
          onLogin={() => {
            // 로그인 성공 (JWT 토큰은 Login 컴포넌트에서 이미 저장됨)
            alert("로그인에 성공하였습니다.");
            router.push("/main");
          }}
          onShowRegister={() => {
            router.push("/register");
          }}
        />
      </LoginHandler>
    </Suspense>
  );
}