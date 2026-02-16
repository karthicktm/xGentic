"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const envStyles: Record<string, string> = {
  development: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  qa: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  staging: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  production: "bg-green-500/20 text-green-400 border-green-500/30",
  sandbox: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30",
};

interface EnvBadgeProps {
  environment: string;
  className?: string;
}

export function EnvBadge({ environment, className }: EnvBadgeProps) {
  const style = envStyles[environment.toLowerCase()] ?? envStyles.sandbox;
  return (
    <Badge variant="outline" className={cn(style, className)}>
      {environment}
    </Badge>
  );
}
