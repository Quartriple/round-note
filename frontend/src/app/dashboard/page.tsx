"use client";

import Link from "next/link";
import {
  SidebarProvider,
  Sidebar,
  SidebarContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
} from "@/shared/ui/sidebar";

export default function DashboardPage() {
  return (
    <SidebarProvider defaultOpen={true}>
      <div className="flex min-h-screen w-full">
        <Sidebar collapsible="offcanvas" side="left" className="shrink-0">
          <SidebarContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton asChild>
                  <Link href="/">대시보드</Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton asChild>
                  <Link href="/meetings">회의록</Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarContent>
        </Sidebar>

        <main className="flex-1 flex justify-center bg-background">
          <div className="w-[1000px] px-4 py-6">
            <h1 className="text-2xl font-semibold mb-4">대시보드</h1>
            <p>여기에 대시보드 콘텐츠를 추가하세요.</p>
          </div>
        </main>
      </div>
    </SidebarProvider>
  );
}
