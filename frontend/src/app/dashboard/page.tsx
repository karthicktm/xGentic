"use client";

import { useQuery } from "@tanstack/react-query";
import { Bot, Cloud, MessageSquare, Users, BarChart3, Activity } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";

interface UsageData {
  total_interactions: number;
  total_duration_seconds: number;
  total_tokens: number;
  total_cost_usd: number;
}

export default function DashboardPage() {
  const { data: usage } = useQuery<UsageData>({
    queryKey: ["usage"],
    queryFn: async () => {
      const res = await api.get("/api/v1/usage");
      return res.data;
    },
  });

  const stats = [
    {
      title: "Total Interactions",
      value: usage?.total_interactions ?? 0,
      icon: MessageSquare,
      color: "text-blue-400",
    },
    {
      title: "Total Duration",
      value: `${Math.round((usage?.total_duration_seconds ?? 0) / 60)}m`,
      icon: Activity,
      color: "text-green-400",
    },
    {
      title: "Tokens Used",
      value: (usage?.total_tokens ?? 0).toLocaleString(),
      icon: BarChart3,
      color: "text-purple-400",
    },
    {
      title: "Total Cost",
      value: `$${(usage?.total_cost_usd ?? 0).toFixed(2)}`,
      icon: Cloud,
      color: "text-amber-400",
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Overview of your xGentic platform usage and activity.
        </p>
      </div>

      {/* Stats Grid */}
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

      {/* Agent Status by Type */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-primary" />
            Agent Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            {["Voice", "Chat", "Email", "Document/Workflow"].map((type) => (
              <Badge key={type} variant="secondary" className="px-3 py-1">
                {type}
              </Badge>
            ))}
          </div>
          <p className="mt-4 text-sm text-muted-foreground">
            Create and deploy agents across multiple environments to get started.
          </p>
        </CardContent>
      </Card>

      {/* Environment Health */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cloud className="h-5 w-5 text-primary" />
            Environment Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            {["Development", "QA", "Staging", "Production"].map((env) => (
              <div key={env} className="flex items-center gap-2 rounded-lg border border-border p-3">
                <div className="h-2 w-2 rounded-full bg-green-500" />
                <span className="text-sm">{env}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
