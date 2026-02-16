"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Puzzle, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";

interface Integration {
  id: string;
  name: string;
  slug: string;
  description: string;
  category: string;
  status: string;
  icon_url?: string;
}

const integrationDefaults: {
  slug: string;
  name: string;
  description: string;
  category: string;
  color: string;
}[] = [
  {
    slug: "servicenow",
    name: "ServiceNow",
    description: "IT service management, incident tracking, and workflow automation.",
    category: "ITSM",
    color: "text-green-400",
  },
  {
    slug: "jira",
    name: "Jira",
    description: "Project tracking, issue management, and agile workflows.",
    category: "Project Management",
    color: "text-blue-400",
  },
  {
    slug: "salesforce",
    name: "Salesforce",
    description: "CRM, sales pipeline, and customer data management.",
    category: "CRM",
    color: "text-cyan-400",
  },
  {
    slug: "confluence",
    name: "Confluence",
    description: "Knowledge base, documentation, and team collaboration.",
    category: "Knowledge",
    color: "text-blue-400",
  },
  {
    slug: "sharepoint",
    name: "SharePoint",
    description: "Document management, intranet, and content collaboration.",
    category: "Documents",
    color: "text-teal-400",
  },
  {
    slug: "teams",
    name: "Microsoft Teams",
    description: "Team messaging, video calls, and collaboration hub.",
    category: "Communication",
    color: "text-purple-400",
  },
  {
    slug: "outlook",
    name: "Microsoft Outlook",
    description: "Email, calendar, and scheduling integration.",
    category: "Email",
    color: "text-blue-400",
  },
  {
    slug: "pagerduty",
    name: "PagerDuty",
    description: "Incident response, alerting, and on-call management.",
    category: "Incident Management",
    color: "text-green-400",
  },
];

export default function IntegrationsPage() {
  const queryClient = useQueryClient();

  const { data: integrations = [] } = useQuery<Integration[]>({
    queryKey: ["integrations"],
    queryFn: async () => {
      const res = await api.get("/api/v1/integrations");
      return res.data;
    },
  });

  const toggleIntegration = useMutation({
    mutationFn: async ({ slug, action }: { slug: string; action: "connect" | "disconnect" }) => {
      const res = await api.post(`/api/v1/integrations/${slug}/${action}`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["integrations"] });
    },
  });

  const getIntegrationStatus = (slug: string): string => {
    const found = integrations.find((i) => i.slug === slug);
    return found?.status ?? "disconnected";
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Integrations</h1>
        <p className="text-sm text-muted-foreground">
          Connect your enterprise tools and services to power agent workflows.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {integrationDefaults.map((integration) => {
          const status = getIntegrationStatus(integration.slug);
          const isConnected = status === "connected" || status === "active";

          return (
            <Card key={integration.slug} className="flex flex-col">
              <CardHeader className="flex-1">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Puzzle className={`h-5 w-5 ${integration.color}`} />
                    <CardTitle className="text-base">{integration.name}</CardTitle>
                  </div>
                  <Badge
                    variant="outline"
                    className={
                      isConnected
                        ? "bg-green-500/20 text-green-400 border-green-500/30"
                        : "bg-zinc-500/20 text-zinc-400 border-zinc-500/30"
                    }
                  >
                    {isConnected ? "Connected" : "Disconnected"}
                  </Badge>
                </div>
                <CardDescription className="mt-2">
                  {integration.description}
                </CardDescription>
                <Badge variant="secondary" className="mt-2 w-fit text-xs">
                  {integration.category}
                </Badge>
              </CardHeader>
              <CardContent className="pt-0">
                {isConnected ? (
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() =>
                        toggleIntegration.mutate({
                          slug: integration.slug,
                          action: "disconnect",
                        })
                      }
                      disabled={toggleIntegration.isPending}
                    >
                      Disconnect
                    </Button>
                    <Button variant="ghost" size="sm">
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </div>
                ) : (
                  <Button
                    size="sm"
                    className="w-full"
                    onClick={() =>
                      toggleIntegration.mutate({
                        slug: integration.slug,
                        action: "connect",
                      })
                    }
                    disabled={toggleIntegration.isPending}
                  >
                    Connect
                  </Button>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
