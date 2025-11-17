import VADTestPage from "@/features/realtime/VADTestPage";
import React from "react";
import Link from "next/link";

/**
 * 백엔드 헬스체크 및 실시간 전사 기능 테스트를 위한 페이지 라우트입니다.
 * /api-test URL로 접근 시 이 컴포넌트가 렌더링됩니다.
 */
export default function ApiTestPage() {
    return (
        <div>
            <div>
                <Link href="/main" style={{
                    color: "black",
                    textDecoration: "none",
                    fontWeight: "bold",
                    fontSize: "14px",
                    padding: "5px 10px",
                    border: "1px solid #61dafb",
                    borderRadius: "4px"
                }}>
                    메인 페이지로 돌아가기
                </Link>
            </div>
            <VADTestPage />
        </div>
    );
}