"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { MessageSquare, Phone, Mail, GitBranch } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import api from "@/lib/api";

interface Interaction {
  id: string;
  interaction_type: string;
  agent_name: string;
  contact_name: string;
  duration_seconds: number;
  status: string;
  created_at: string;
}

const interactionTypes = ["all", "voice", "chat", "email", "workflow"] as const;

const statusColor: Record<string, string> = {
  completed: "bg-green-500/20 text-green-400 border-green-500/30",
  in_progress: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  failed: "bg-red-500/20 text-red-400 border-red-500/30",
  abandoned: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30",
};

const typeIcon: Record<string, React.ElementType> = {
  voice: Phone,
  chat: MessageSquare,
  email: Mail,
  workflow: GitBranch,
};

const typeColor: Record<string, string> = {
  voice: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  chat: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  email: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  workflow: "bg-green-500/20 text-green-400 border-green-500/30",
};

function formatDuration(seconds: number): string {
  if (!seconds) return "---";
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
}

export default function InteractionsPage() {
  const [activeTab, setActiveTab] = useState<string>("all");

  const { data: interactions = [], isLoading } = useQuery<Interaction[]>({
    queryKey: ["interactions", activeTab],
    queryFn: async () => {
      const params = activeTab !== "all" ? `?interaction_type=${activeTab}` : "";
      const res = await api.get(`/api/v1/interactions${params}`);
      return res.data;
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Interactions</h1>
        <p className="text-sm text-muted-foreground">
          View the history of all agent interactions across channels.
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          {interactionTypes.map((type) => (
            <TabsTrigger key={type} value={type} className="capitalize">
              {type === "all" ? "All" : type}
            </TabsTrigger>
          ))}
        </TabsList>

        {interactionTypes.map((type) => (
          <TabsContent key={type} value={type}>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5 text-primary" />
                  {type === "all"
                    ? "All Interactions"
                    : `${type.charAt(0).toUpperCase() + type.slice(1)} Interactions`}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <p className="text-sm text-muted-foreground">Loading interactions...</p>
                ) : interactions.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No interactions found.
                  </p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Type</TableHead>
                        <TableHead>Agent</TableHead>
                        <TableHead>Contact</TableHead>
                        <TableHead>Duration</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Date</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {interactions.map((interaction) => {
                        const TypeIcon = typeIcon[interaction.interaction_type] ?? MessageSquare;
                        return (
                          <TableRow key={interaction.id}>
                            <TableCell>
                              <Badge
                                variant="outline"
                                className={typeColor[interaction.interaction_type] ?? ""}
                              >
                                <TypeIcon className="mr-1 h-3 w-3" />
                                {interaction.interaction_type}
                              </Badge>
                            </TableCell>
                            <TableCell className="font-medium">
                              {interaction.agent_name}
                            </TableCell>
                            <TableCell className="text-muted-foreground">
                              {interaction.contact_name ?? "---"}
                            </TableCell>
                            <TableCell className="text-muted-foreground">
                              {formatDuration(interaction.duration_seconds)}
                            </TableCell>
                            <TableCell>
                              <Badge
                                variant="outline"
                                className={statusColor[interaction.status] ?? ""}
                              >
                                {interaction.status}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-muted-foreground">
                              {new Date(interaction.created_at).toLocaleString()}
                            </TableCell>
                          </TableRow>
                        );
                      })}
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
