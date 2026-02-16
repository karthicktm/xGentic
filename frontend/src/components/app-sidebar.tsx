"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  Building2,
  Layers,
  FolderTree,
  FolderKanban,
  Boxes,
  Bot,
  Cloud,
  Users,
  MessageSquare,
  Plug,
  Shield,
  BarChart3,
  FileText,
  Settings,
  ChevronLeft,
  LogOut,
  User,
} from "lucide-react";
import { useSidebarStore } from "@/lib/sidebar-store";
import { useAuth } from "@/hooks/use-auth";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  adminOnly?: boolean;
  group: string;
}

const navItems: NavItem[] = [
  // Overview
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard, group: "Overview" },
  // Organization
  { name: "Units", href: "/dashboard/units", icon: Building2, group: "Organization" },
  { name: "Departments", href: "/dashboard/departments", icon: Layers, group: "Organization" },
  { name: "Projects", href: "/dashboard/projects", icon: FolderTree, group: "Organization" },
  { name: "Workspaces", href: "/dashboard/workspaces", icon: FolderKanban, group: "Organization" },
  // Agents
  { name: "All Agents", href: "/dashboard/agents", icon: Bot, group: "Agents" },
  { name: "Environments", href: "/dashboard/environments", icon: Cloud, group: "Agents" },
  // Operations
  { name: "Interactions", href: "/dashboard/interactions", icon: MessageSquare, group: "Operations" },
  { name: "Integrations", href: "/dashboard/integrations", icon: Plug, group: "Operations" },
  // Administration
  { name: "Users", href: "/dashboard/users", icon: Users, adminOnly: true, group: "Administration" },
  { name: "Usage & Quotas", href: "/dashboard/usage", icon: BarChart3, group: "Administration" },
  { name: "Audit Logs", href: "/dashboard/audit-logs", icon: FileText, adminOnly: true, group: "Administration" },
  { name: "Compliance", href: "/dashboard/compliance", icon: Shield, group: "Administration" },
  { name: "Settings", href: "/dashboard/settings", icon: Settings, group: "Administration" },
];

export function AppSidebar() {
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar } = useSidebarStore();
  const { user, logout, isAdmin } = useAuth();

  const filteredItems = navItems.filter((item) => !item.adminOnly || isAdmin);

  // Group items
  const groups = filteredItems.reduce<Record<string, NavItem[]>>((acc, item) => {
    if (!acc[item.group]) acc[item.group] = [];
    acc[item.group].push(item);
    return acc;
  }, {});

  return (
    <motion.aside
      animate={{ width: sidebarOpen ? 240 : 64 }}
      transition={{ duration: 0.2, ease: "easeInOut" }}
      className="fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-sidebar-border bg-sidebar"
    >
      {/* Logo */}
      <div className="flex h-14 items-center gap-2 border-b border-sidebar-border px-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
          <Boxes className="h-4 w-4 text-primary" />
        </div>
        {sidebarOpen && (
          <motion.span
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-lg font-bold text-sidebar-foreground"
          >
            xGentic
          </motion.span>
        )}
        <button
          onClick={toggleSidebar}
          className="ml-auto flex h-6 w-6 items-center justify-center rounded text-sidebar-foreground/60 hover:text-sidebar-foreground"
        >
          <ChevronLeft
            className={`h-4 w-4 transition-transform ${!sidebarOpen ? "rotate-180" : ""}`}
          />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-2 py-3">
        {Object.entries(groups).map(([group, items]) => (
          <div key={group} className="mb-4">
            {sidebarOpen && (
              <p className="mb-1 px-3 text-[10px] font-semibold uppercase tracking-wider text-sidebar-foreground/40">
                {group}
              </p>
            )}
            {items.map((item) => {
              const isActive =
                pathname === item.href ||
                (item.href !== "/dashboard" && pathname.startsWith(item.href));
              const Icon = item.icon;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`group relative mb-0.5 flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                    isActive
                      ? "bg-sidebar-accent text-sidebar-accent-foreground"
                      : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
                  }`}
                >
                  {isActive && (
                    <motion.div
                      layoutId="sidebar-active"
                      className="absolute left-0 top-1 h-6 w-0.5 rounded-full bg-primary"
                      transition={{ type: "spring", stiffness: 300, damping: 30 }}
                    />
                  )}
                  <Icon
                    className={`h-4 w-4 shrink-0 ${isActive ? "text-primary" : ""}`}
                  />
                  {sidebarOpen && <span className="truncate">{item.name}</span>}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      {/* User section */}
      <div className="border-t border-sidebar-border p-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground">
              <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/20">
                <User className="h-3 w-3 text-primary" />
              </div>
              {sidebarOpen && (
                <span className="truncate">{user?.full_name ?? user?.email ?? "User"}</span>
              )}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuItem asChild>
              <Link href="/dashboard/settings">
                <Settings className="mr-2 h-4 w-4" />
                Settings
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={logout} className="text-destructive">
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </motion.aside>
  );
}
