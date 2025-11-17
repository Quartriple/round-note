"use client";

import { useRouter } from "next/navigation";
import { Login } from "@/features/auth/Login";

export default function LoginPage() {
  const router = useRouter();

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