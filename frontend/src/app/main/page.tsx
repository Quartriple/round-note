"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Dashboard from "@/features/dashboard/Dashboard";

export default function MainPage() {
  const router = useRouter();

  useEffect(() => {
    const loggedInUser = localStorage.getItem("roundnote-loggedin");
    if (!loggedInUser) {
      router.replace("/login");
    }
  }, [router]);

  return (
    <div>
      {/* <div style={{ padding: "10px", backgroundColor: "#1e1e1e", borderBottom: "1px solid #444", textAlign: "center" }}>
        <Link
          href="/api-test"
          style={{
            color: "#61dafb",
            textDecoration: "none",
            fontWeight: "bold",
            fontSize: "14px",
            padding: "5px 10px",
            border: "1px solid #61dafb",
            borderRadius: "4px"
          }}
        >
          🚀 VAD 기능 테스트 페이지 (백엔드 테스트용)
        </Link>
      </div> */}
      <Dashboard />
    </div>
  );
}