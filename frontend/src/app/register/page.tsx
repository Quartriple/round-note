"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Register } from "@/features/auth/Register";

export default function RegisterPage() {
  const router = useRouter();

  useEffect(() => {
    // 이미 로그인되어 있는지 확인
    const token = localStorage.getItem('access_token');
    if (token) {
      router.replace("/main");
    }
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-primary/10 via-white to-blue-50 p-4">
      <Register
        onRegister={() => {
          alert("회원가입에 성공하였습니다.");
          // 회원가입 후 메인 페이지로 이동 (토큰은 Register 컴포넌트에서 이미 저장됨)
          router.push("/main");
        }}
        onBackToLogin={() => {
          router.push("/login");
        }}
      />
    </div>
  );
}