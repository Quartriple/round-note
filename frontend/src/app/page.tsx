"use client";

import { useRouter } from "next/navigation";
import { Login } from "@/features/auth/Login";
import VADTestPage from "@/features/realtime/VADTestPage";

export default function Page() {
  const router = useRouter();

  return (
    <Login
    onLogin={() => {
      router.push("/main"); // 로그인 성공 시 메인으로 이동
    }}
    onShowRegister={() => {
      router.push("/register"); // 회원가입 페이지로 이동
    }}
    />
    // <VADTestPage />
  );
}