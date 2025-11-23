"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Login } from "@/features/auth/Login";
import { useEffect, Suspense } from "react";

// useSearchParams를 사용하는 컴포넌트를 분리
function LoginHandler({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    // Google OAuth는 백엔드에서 자동으로 Cookie를 설정하고 리다이렉트함
    // 이미 로그인되어 있는지 확인 (선택적)
    async function checkExistingAuth() {
      const { checkAuth } = await import('@/utils/auth');
      const user = await checkAuth();
      if (user) {
        router.replace("/main");
      }
    }
    
    checkExistingAuth();
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