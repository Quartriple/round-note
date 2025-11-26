import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  turbopack: {
    // frontend 디렉터리가 프로젝트 루트라면 __dirname 그대로 사용
    root: __dirname,
  },
};

export default nextConfig;