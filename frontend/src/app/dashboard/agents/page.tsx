"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { Bot, Plus, Cloud, Download } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import api from "@/lib/api";

interface Agent {
  id: string;
  name: string;
  agent_type: string;
  status: string;
  environment: string;
  total_interactions: number;
  agent_source: string;
  azure_foundry_agent_id: string | null;
  updated_at: string;
}

const agentTypes = ["all", "voice", "chat", "email", "workflow"] as const;

const statusColor: Record<string, string> = {
  active: "bg-green-500/20 text-green-400 border-green-500/30",
  inactive: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30",
  draft: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  error: "bg-red-500/20 text-red-400 border-red-500/30",
};

const typeColor: Record<string, string> = {
  voice: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  chat: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  email: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  workflow: "bg-green-500/20 text-green-400 border-green-500/30",
};

export default function AgentsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<string>("all");
  const [importOpen, setImportOpen] = useState(false);
  const [importForm, setImportForm] = useState({
    name: "",
    azure_foundry_agent_id: "",
    agent_type: "chat",
    model: "gpt-4o",
  });

  const { data: agents = [], isLoading } = useQuery<Agent[]>({
    queryKey: ["agents", activeTab],
    queryFn: async () => {
      const params = activeTab !== "all" ? `?agent_type=${activeTab}` : "";
      const res = await api.get(`/api/v1/agents${params}`);
      return res.data;
    },
  });

  const importAgent = useMutation({
    mutationFn: async (data: typeof importForm) => {
      const res = await api.post("/api/v1/azure-foundry/import-agent", data);
      return res.data;
    },
    onSuccess: () => {
      setImportOpen(false);
      setImportForm({ name: "", azure_foundry_agent_id: "", agent_type: "chat", model: "gpt-4o" });
      void queryClient.invalidateQueries({ queryKey: ["agents"] });
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Agents</h1>
          <p className="text-sm text-muted-foreground">
            Manage your AI agents across voice, chat, email, and workflow types.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Dialog open={importOpen} onOpenChange={setImportOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Download className="mr-2 h-4 w-4" />
                Import from Azure
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Import Azure Foundry Agent</DialogTitle>
                <DialogDescription>
                  Import an existing agent configuration from Azure AI Foundry.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="import-name">Agent Name</Label>
                  <Input
                    id="import-name"
                    placeholder="e.g. Support Agent"
                    value={importForm.name}
                    onChange={(e) => setImportForm({ ...importForm, name: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="import-agent-id">Azure Foundry Agent ID</Label>
                  <Input
                    id="import-agent-id"
                    placeholder="e.g. azure_agent_12345"
                    value={importForm.azure_foundry_agent_id}
                    onChange={(e) =>
                      setImportForm({ ...importForm, azure_foundry_agent_id: e.target.value })
                    }
                  />
                </div>
                <Button
                  className="w-full"
                  onClick={() => importAgent.mutate(importForm)}
                  disabled={
                    !importForm.name.trim() ||
                    !importForm.azure_foundry_agent_id.trim() ||
                    importAgent.isPending
                  }
                >
                  {importAgent.isPending ? "Importing..." : "Import Agent"}
                </Button>
                {importAgent.isError && (
                  <p className="text-sm text-red-400">Failed to import agent. Please try again.</p>
                )}
              </div>
            </DialogContent>
          </Dialog>
          <Button onClick={() => router.push("/dashboard/agents/new")}>
            <Plus className="mr-2 h-4 w-4" />
            New Agent
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          {agentTypes.map((type) => (
            <TabsTrigger key={type} value={type} className="capitalize">
              {type === "all" ? "All" : type}
            </TabsTrigger>
          ))}
        </TabsList>

        {agentTypes.map((type) => (
          <TabsContent key={type} value={type}>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bot className="h-5 w-5 text-primary" />
                  {type === "all" ? "All Agents" : `${type.charAt(0).toUpperCase() + type.slice(1)} Agents`}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <p className="text-sm text-muted-foreground">Loading agents...</p>
                ) : agents.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No agents found. Create a new agent to get started.
                  </p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Source</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Environment</TableHead>
                        <TableHead className="text-right">Interactions</TableHead>
                        <TableHead>Last Updated</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {agents.map((agent) => (
                        <TableRow
                          key={agent.id}
                          className="cursor-pointer"
                          onClick={() => router.push(`/dashboard/agents/${agent.id}`)}
                        >
                          <TableCell className="font-medium">{agent.name}</TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className={typeColor[agent.agent_type] ?? ""}
                            >
                              {agent.agent_type}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {agent.agent_source === "azure_foundry" ? (
                              <Badge
                                variant="outline"
                                className="bg-sky-500/20 text-sky-400 border-sky-500/30"
                              >
                                <Cloud className="mr-1 h-3 w-3" />
                                Azure
                              </Badge>
                            ) : (
                              <Badge variant="outline" className="text-muted-foreground">
                                Local
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className={statusColor[agent.status] ?? ""}
                            >
                              {agent.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {agent.environment ?? "---"}
                          </TableCell>
                          <TableCell className="text-right">
                            {agent.total_interactions?.toLocaleString() ?? 0}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {new Date(agent.updated_at).toLocaleDateString()}
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
