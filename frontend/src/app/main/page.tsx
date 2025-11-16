"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Dashboard from "@/features/dashboard/Dashboard";

export default function MainPage() {
  const router = useRouter();

    useEffect(() => {
    const loggedInUser = localStorage.getItem("roundnote-loggedin");
    if (!loggedInUser) {
        router.replace("/login"); // alert 대신 바로 이동
    }
    }, [router]);

  return <Dashboard />;  // 🔥 여기에서 바로 렌더링
}

// react-router-dom