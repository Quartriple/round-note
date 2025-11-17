import { ReactNode } from "react";
import { SidebarProvider, Sidebar } from "@/shared/ui/sidebar";

export default function MainLayout({ children }: { children: ReactNode }) {
  return (
    <SidebarProvider>
      <div className="flex">
        <Sidebar>
          {/* 사이드바 안에 들어갈 메뉴들 */}
        </Sidebar>
        <main className="flex-1 p-6">{children}</main>
      </div>
    </SidebarProvider>
  );
}