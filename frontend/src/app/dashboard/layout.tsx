"use client";

import { AppSidebar } from "@/components/app-sidebar";
import { TopBar } from "@/components/top-bar";
import { useSidebarStore } from "@/lib/sidebar-store";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { sidebarOpen } = useSidebarStore();

  return (
    <div className="flex min-h-screen">
      <AppSidebar />
      <main
        className="flex-1 transition-all duration-200"
        style={{ marginLeft: sidebarOpen ? 240 : 64 }}
      >
        <TopBar />
        <div className="p-6">{children}</div>
      </main>
    </div>
  );
}
