"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import api from "@/lib/api";
import { useHierarchyStore } from "@/lib/hierarchy-store";

interface User {
  id: number;
  email: string;
  full_name: string | null;
  role: "super_admin" | "org_admin" | "manager" | "user";
  provider: string;
  organization_id: string | null;
  email_verified: boolean;
  is_active: boolean;
  department: string | null;
  job_title: string | null;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    fullName: string,
    organizationName?: string
  ) => Promise<void>;
  loginWithSSO: (idToken: string, provider?: string) => Promise<void>;
  logout: () => void;
  isSuperAdmin: boolean;
  isAdmin: boolean;
  isManager: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

const PUBLIC_PATHS = ["/", "/login", "/register", "/forgot-password", "/reset-password"];

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();
  const { setOrganization } = useHierarchyStore();

  // Load user on mount
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    const isPublicPage = PUBLIC_PATHS.includes(pathname) || pathname.startsWith("/embed");

    if (!token) {
      setLoading(false);
      if (!isPublicPage) {
        router.push("/login");
      }
      return;
    }

    api
      .get("/api/v1/auth/me")
      .then(async (res) => {
        setUser(res.data);

        // Load user's organization into hierarchy store
        if (res.data.organization_id) {
          try {
            const orgRes = await api.get(`/api/v1/organizations/${res.data.organization_id}`);
            setOrganization(orgRes.data.id, orgRes.data.name);
          } catch (error) {
            console.error("Failed to load organization:", error);
          }
        }
      })
      .catch(() => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        if (!isPublicPage) {
          router.push("/login");
        }
      })
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Redirect authenticated users away from login/register
  useEffect(() => {
    if (!loading && user && (pathname === "/login" || pathname === "/register")) {
      router.push("/dashboard");
    }
  }, [loading, user, pathname, router]);

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await api.post("/api/v1/auth/login", { email, password });
      localStorage.setItem("access_token", res.data.access_token);
      localStorage.setItem("refresh_token", res.data.refresh_token);
      setUser(res.data.user);

      // Load organization into hierarchy store
      if (res.data.user.organization_id) {
        try {
          const orgRes = await api.get(`/api/v1/organizations/${res.data.user.organization_id}`);
          setOrganization(orgRes.data.id, orgRes.data.name);
        } catch (error) {
          console.error("Failed to load organization:", error);
        }
      }

      router.push("/dashboard");
    },
    [router, setOrganization]
  );

  const register = useCallback(
    async (email: string, password: string, fullName: string, organizationName?: string) => {
      const res = await api.post("/api/v1/auth/register", {
        email,
        password,
        full_name: fullName,
        organization_name: organizationName,
      });
      localStorage.setItem("access_token", res.data.access_token);
      localStorage.setItem("refresh_token", res.data.refresh_token);
      setUser(res.data.user);
      router.push("/dashboard");
    },
    [router]
  );

  const loginWithSSO = useCallback(
    async (idToken: string, provider = "azure_ad") => {
      const res = await api.post("/api/v1/auth/sso-login", {
        id_token: idToken,
        provider,
      });
      localStorage.setItem("access_token", res.data.access_token);
      localStorage.setItem("refresh_token", res.data.refresh_token);
      setUser(res.data.user);
      router.push("/dashboard");
    },
    [router]
  );

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
    router.push("/login");
  }, [router]);

  const value = useMemo(
    () => ({
      user,
      loading,
      login,
      register,
      loginWithSSO,
      logout,
      isSuperAdmin: user?.role === "super_admin",
      isAdmin: user?.role === "super_admin" || user?.role === "org_admin",
      isManager:
        user?.role === "super_admin" ||
        user?.role === "org_admin" ||
        user?.role === "manager",
    }),
    [user, loading, login, register, loginWithSSO, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
