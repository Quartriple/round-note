"use client";

import { Register } from "@/features/auth/Register";

export default function RegisterPage() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-primary/10 via-white to-blue-50 p-4">
      <Register
        onRegister={() => {
          alert("회원가입에 성공하였습니다.");
          // 회원가입 후 로그인 페이지로 이동
          window.location.href = "/login";
        }}
        onBackToLogin={() => {
          window.location.href = "/login";
        }}
      />
    </div>
  );
}