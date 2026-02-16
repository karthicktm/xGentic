"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Megaphone, Play, Pause, StopCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import api from "@/lib/api";

interface Campaign {
  id: string;
  name: string;
  campaign_type: string;
  status: string;
  total_contacts: number;
  completed_contacts: number;
  created_at: string;
}

const campaignTypes = ["all", "voice", "chat", "email"] as const;

const statusColor: Record<string, string> = {
  active: "bg-green-500/20 text-green-400 border-green-500/30",
  running: "bg-green-500/20 text-green-400 border-green-500/30",
  paused: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  completed: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  draft: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30",
  failed: "bg-red-500/20 text-red-400 border-red-500/30",
};

const typeColor: Record<string, string> = {
  voice: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  chat: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  email: "bg-amber-500/20 text-amber-400 border-amber-500/30",
};

export default function CampaignsPage() {
  const [activeTab, setActiveTab] = useState<string>("all");

  const { data: campaigns = [], isLoading } = useQuery<Campaign[]>({
    queryKey: ["campaigns", activeTab],
    queryFn: async () => {
      const params = activeTab !== "all" ? `?campaign_type=${activeTab}` : "";
      const res = await api.get(`/api/v1/campaigns${params}`);
      return res.data;
    },
  });

  const getProgress = (c: Campaign) => {
    if (!c.total_contacts || c.total_contacts === 0) return 0;
    return Math.round((c.completed_contacts / c.total_contacts) * 100);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Campaigns</h1>
          <p className="text-sm text-muted-foreground">
            Manage outreach campaigns across voice, chat, and email channels.
          </p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          {campaignTypes.map((type) => (
            <TabsTrigger key={type} value={type} className="capitalize">
              {type === "all" ? "All" : type}
            </TabsTrigger>
          ))}
        </TabsList>

        {campaignTypes.map((type) => (
          <TabsContent key={type} value={type}>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Megaphone className="h-5 w-5 text-primary" />
                  {type === "all"
                    ? "All Campaigns"
                    : `${type.charAt(0).toUpperCase() + type.slice(1)} Campaigns`}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <p className="text-sm text-muted-foreground">Loading campaigns...</p>
                ) : campaigns.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No campaigns found.
                  </p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Progress</TableHead>
                        <TableHead className="w-32">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {campaigns.map((campaign) => (
                        <TableRow key={campaign.id}>
                          <TableCell className="font-medium">{campaign.name}</TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className={typeColor[campaign.campaign_type] ?? ""}
                            >
                              {campaign.campaign_type}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className={statusColor[campaign.status] ?? ""}
                            >
                              {campaign.status}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Progress value={getProgress(campaign)} className="h-2 w-24" />
                              <span className="text-xs text-muted-foreground">
                                {getProgress(campaign)}%
                              </span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex gap-1">
                              {campaign.status === "paused" || campaign.status === "draft" ? (
                                <Button variant="ghost" size="sm" title="Start">
                                  <Play className="h-4 w-4 text-green-400" />
                                </Button>
                              ) : campaign.status === "running" || campaign.status === "active" ? (
                                <Button variant="ghost" size="sm" title="Pause">
                                  <Pause className="h-4 w-4 text-amber-400" />
                                </Button>
                              ) : null}
                              {campaign.status !== "completed" && campaign.status !== "failed" && (
                                <Button variant="ghost" size="sm" title="Stop">
                                  <StopCircle className="h-4 w-4 text-red-400" />
                                </Button>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
