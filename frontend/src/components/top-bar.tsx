"use client";

import { ChevronRight } from "lucide-react";
import { useHierarchyStore } from "@/lib/hierarchy-store";
import { useEnvironmentStore } from "@/lib/environment-store";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";

interface Environment {
  id: string;
  name: string;
  type: string;
  is_active: boolean;
}

const envTypeColors: Record<string, string> = {
  development: "bg-blue-500/20 text-blue-400",
  qa: "bg-amber-500/20 text-amber-400",
  staging: "bg-purple-500/20 text-purple-400",
  production: "bg-green-500/20 text-green-400",
  sandbox: "bg-gray-500/20 text-gray-400",
};

export function TopBar() {
  const hierarchy = useHierarchyStore();
  const { environmentId, environmentName, environmentType, setEnvironment } =
    useEnvironmentStore();

  const { data: environments } = useQuery<Environment[]>({
    queryKey: ["environments"],
    queryFn: async () => {
      const res = await api.get("/api/v1/environments");
      return res.data;
    },
  });

  const breadcrumbs = [
    hierarchy.organizationName && { label: hierarchy.organizationName, type: "Org" },
    hierarchy.unitName && { label: hierarchy.unitName, type: "Unit" },
    hierarchy.departmentName && { label: hierarchy.departmentName, type: "Dept" },
    hierarchy.projectName && { label: hierarchy.projectName, type: "Project" },
    hierarchy.workspaceName && { label: hierarchy.workspaceName, type: "Workspace" },
  ].filter(Boolean) as Array<{ label: string; type: string }>;

  return (
    <div className="flex h-12 items-center justify-between border-b border-border bg-card/50 px-4">
      {/* Hierarchy breadcrumb */}
      <div className="flex items-center gap-1 text-sm">
        {breadcrumbs.length === 0 ? (
          <span className="text-muted-foreground">Select organization context...</span>
        ) : (
          breadcrumbs.map((crumb, i) => (
            <div key={crumb.type} className="flex items-center gap-1">
              {i > 0 && <ChevronRight className="h-3 w-3 text-muted-foreground/50" />}
              <span className="text-muted-foreground/60 text-[10px] uppercase">{crumb.type}:</span>
              <span className="text-foreground">{crumb.label}</span>
            </div>
          ))
        )}
      </div>

      {/* Environment switcher */}
      <div className="flex items-center gap-2">
        {environmentType && (
          <Badge
            variant="secondary"
            className={envTypeColors[environmentType] ?? "bg-gray-500/20 text-gray-400"}
          >
            {environmentType}
          </Badge>
        )}
        <Select
          value={environmentId ?? undefined}
          onValueChange={(id) => {
            const env = environments?.find((e) => e.id === id);
            if (env) {
              setEnvironment(env.id, env.name, env.type);
            }
          }}
        >
          <SelectTrigger className="h-8 w-44 text-xs">
            <SelectValue placeholder="Environment" />
          </SelectTrigger>
          <SelectContent>
            {environments?.map((env) => (
              <SelectItem key={env.id} value={env.id}>
                <div className="flex items-center gap-2">
                  <div
                    className={`h-2 w-2 rounded-full ${
                      env.type === "production"
                        ? "bg-green-500"
                        : env.type === "staging"
                          ? "bg-purple-500"
                          : env.type === "qa"
                            ? "bg-amber-500"
                            : "bg-blue-500"
                    }`}
                  />
                  {env.name}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
