"use client";

import { useQuery } from "@tanstack/react-query";
import { BarChart3, Activity, MessageSquare, Clock, DollarSign } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import api from "@/lib/api";

interface UsageData {
  total_interactions: number;
  total_duration_seconds: number;
  total_tokens: number;
  total_cost_usd: number;
  period_start: string;
  period_end: string;
}

interface Quota {
  name: string;
  type: string;
  used: number;
  limit: number;
  unit: string;
}

export default function UsagePage() {
  const { data: usage } = useQuery<UsageData>({
    queryKey: ["usage"],
    queryFn: async () => {
      const res = await api.get("/api/v1/usage");
      return res.data;
    },
  });

  const { data: quotas = [] } = useQuery<Quota[]>({
    queryKey: ["usage-quotas"],
    queryFn: async () => {
      const res = await api.get("/api/v1/usage/quotas");
      return res.data;
    },
  });

  const stats = [
    {
      title: "Total Interactions",
      value: usage?.total_interactions?.toLocaleString() ?? "0",
      icon: MessageSquare,
      color: "text-blue-400",
    },
    {
      title: "Total Duration",
      value: `${Math.round((usage?.total_duration_seconds ?? 0) / 60)} min`,
      icon: Clock,
      color: "text-green-400",
    },
    {
      title: "Tokens Used",
      value: (usage?.total_tokens ?? 0).toLocaleString(),
      icon: Activity,
      color: "text-purple-400",
    },
    {
      title: "Total Cost",
      value: `$${(usage?.total_cost_usd ?? 0).toFixed(2)}`,
      icon: DollarSign,
      color: "text-amber-400",
    },
  ];

  const getProgressColor = (pct: number): string => {
    if (pct >= 90) return "bg-red-500";
    if (pct >= 70) return "bg-amber-500";
    return "bg-primary";
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Usage &amp; Quotas</h1>
        <p className="text-sm text-muted-foreground">
          Monitor your platform usage and resource quotas.
          {usage?.period_start && usage?.period_end && (
            <span>
              {" "}
              Current period: {new Date(usage.period_start).toLocaleDateString()} &ndash;{" "}
              {new Date(usage.period_end).toLocaleDateString()}
            </span>
          )}
        </p>
      </div>

      {/* Overview Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.title}
                </CardTitle>
                <Icon className={`h-4 w-4 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Quotas */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            Resource Quotas
          </CardTitle>
          <CardDescription>
            Track your resource usage against allocated quotas.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {quotas.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No quota information available.
            </p>
          ) : (
            quotas.map((quota) => {
              const pct = quota.limit > 0 ? Math.round((quota.used / quota.limit) * 100) : 0;
              return (
                <div key={quota.type} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium">{quota.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {quota.used.toLocaleString()} / {quota.limit.toLocaleString()} {quota.unit}
                      </p>
                    </div>
                    <span
                      className={`text-sm font-medium ${
                        pct >= 90 ? "text-red-400" : pct >= 70 ? "text-amber-400" : "text-green-400"
                      }`}
                    >
                      {pct}%
                    </span>
                  </div>
                  <Progress
                    value={pct}
                    className="h-2"
                    indicatorClassName={getProgressColor(pct)}
                  />
                </div>
              );
            })
          )}
        </CardContent>
      </Card>
    </div>
  );
}
