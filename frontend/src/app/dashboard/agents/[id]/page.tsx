"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Save,
  Upload,
  Trash2,
  Rocket,
  FileText,
  Cloud,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import { Checkbox } from "@/components/ui/checkbox";
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

interface Agent {
  id: string;
  name: string;
  description: string;
  agent_type: string;
  status: string;
  system_prompt: string;
  temperature: number;
  max_tokens: number;
  provider_type: string;
  provider_config: Record<string, unknown>;
  agent_source: string;
  azure_foundry_agent_id: string | null;
  tools: string[];
  knowledge_base: { id: string; name: string; size: number; uploaded_at: string }[];
  deployments: {
    id: string;
    environment: string;
    status: string;
    version: string;
    deployed_at: string;
  }[];
  updated_at: string;
}

const availableTools = [
  { id: "crm_lookup", label: "CRM Lookup", description: "Search and retrieve CRM contact records" },
  { id: "crm_update", label: "CRM Update", description: "Update CRM contact and deal records" },
  { id: "send_sms", label: "Send SMS", description: "Send SMS messages to contacts" },
  { id: "send_email", label: "Send Email", description: "Send email to contacts" },
  { id: "calendar_check", label: "Calendar Check", description: "Check calendar availability" },
  { id: "calendar_book", label: "Calendar Book", description: "Book calendar appointments" },
  { id: "knowledge_search", label: "Knowledge Search", description: "Search uploaded knowledge base documents" },
  { id: "escalate", label: "Escalate", description: "Escalate to a human agent" },
  { id: "webhook", label: "Webhook", description: "Call an external webhook endpoint" },
  { id: "jira_create", label: "Jira Create Ticket", description: "Create Jira tickets" },
  { id: "servicenow_incident", label: "ServiceNow Incident", description: "Create ServiceNow incidents" },
];

const envColor: Record<string, string> = {
  development: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  qa: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  staging: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  production: "bg-green-500/20 text-green-400 border-green-500/30",
};

export default function AgentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const agentId = params.id as string;

  const { data: agent, isLoading } = useQuery<Agent>({
    queryKey: ["agent", agentId],
    queryFn: async () => {
      const res = await api.get(`/api/v1/agents/${agentId}`);
      return res.data;
    },
  });

  const [editForm, setEditForm] = useState<Partial<Agent>>({});
  const [enabledTools, setEnabledTools] = useState<string[]>([]);

  // Sync state once loaded
  const initialized = agent && Object.keys(editForm).length === 0;
  if (initialized) {
    setEditForm({
      name: agent.name,
      description: agent.description,
      system_prompt: agent.system_prompt,
      temperature: agent.temperature,
      max_tokens: agent.max_tokens,
    });
    setEnabledTools(agent.tools ?? []);
  }

  const updateAgent = useMutation({
    mutationFn: async (data: Partial<Agent>) => {
      const res = await api.patch(`/api/v1/agents/${agentId}`, data);
      return res.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["agent", agentId] });
    },
  });

  const promoteDeployment = useMutation({
    mutationFn: async (deploymentId: string) => {
      const res = await api.post(`/api/v1/agents/${agentId}/deployments/${deploymentId}/promote`);
      return res.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["agent", agentId] });
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <p className="text-sm text-muted-foreground">Loading agent...</p>
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="space-y-6">
        <p className="text-sm text-muted-foreground">Agent not found.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.push("/dashboard/agents")}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold">{agent.name}</h1>
            {agent.agent_source === "azure_foundry" && (
              <Badge variant="outline" className="bg-sky-500/20 text-sky-400 border-sky-500/30">
                <Cloud className="mr-1 h-3 w-3" />
                Azure Foundry
              </Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground">
            {agent.agent_type} agent
            {agent.provider_type ? ` — ${agent.provider_type}` : ""}
            {(agent.provider_config as Record<string, string>)?.model
              ? ` (${(agent.provider_config as Record<string, string>).model})`
              : ""}
            {" "}&mdash; Last updated{" "}
            {new Date(agent.updated_at).toLocaleDateString()}
          </p>
        </div>
      </div>

      <Tabs defaultValue="settings">
        <TabsList>
          <TabsTrigger value="settings">Settings</TabsTrigger>
          <TabsTrigger value="tools">Tools</TabsTrigger>
          <TabsTrigger value="knowledge">Knowledge Base</TabsTrigger>
          <TabsTrigger value="deployments">Deployments</TabsTrigger>
        </TabsList>

        {/* Settings Tab */}
        <TabsContent value="settings">
          <Card>
            <CardHeader>
              <CardTitle>Agent Settings</CardTitle>
              <CardDescription>Update agent configuration and behavior.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  value={editForm.name ?? ""}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Input
                  id="description"
                  value={editForm.description ?? ""}
                  onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="system_prompt">System Prompt</Label>
                <Textarea
                  id="system_prompt"
                  rows={8}
                  value={editForm.system_prompt ?? ""}
                  onChange={(e) => setEditForm({ ...editForm, system_prompt: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label>Temperature: {(editForm.temperature ?? 0.7).toFixed(2)}</Label>
                <Slider
                  min={0}
                  max={2}
                  step={0.01}
                  value={[editForm.temperature ?? 0.7]}
                  onValueChange={([val]) => setEditForm({ ...editForm, temperature: val })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="max_tokens">Max Tokens</Label>
                <Input
                  id="max_tokens"
                  type="number"
                  value={editForm.max_tokens ?? 4096}
                  onChange={(e) =>
                    setEditForm({ ...editForm, max_tokens: parseInt(e.target.value) || 4096 })
                  }
                />
              </div>

              <Button
                onClick={() => updateAgent.mutate(editForm)}
                disabled={updateAgent.isPending}
              >
                <Save className="mr-2 h-4 w-4" />
                {updateAgent.isPending ? "Saving..." : "Save Changes"}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tools Tab */}
        <TabsContent value="tools">
          <Card>
            <CardHeader>
              <CardTitle>Enabled Tools</CardTitle>
              <CardDescription>
                Select which tools this agent can use during interactions.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {availableTools.map((tool) => (
                <div
                  key={tool.id}
                  className="flex items-start gap-3 rounded-lg border border-border p-4"
                >
                  <Checkbox
                    id={tool.id}
                    checked={enabledTools.includes(tool.id)}
                    onCheckedChange={(checked) => {
                      setEnabledTools(
                        checked
                          ? [...enabledTools, tool.id]
                          : enabledTools.filter((t) => t !== tool.id)
                      );
                    }}
                  />
                  <div>
                    <Label htmlFor={tool.id} className="cursor-pointer font-medium">
                      {tool.label}
                    </Label>
                    <p className="text-sm text-muted-foreground">{tool.description}</p>
                  </div>
                </div>
              ))}
              <Button
                onClick={() => updateAgent.mutate({ tools: enabledTools } as Partial<Agent>)}
                disabled={updateAgent.isPending}
              >
                <Save className="mr-2 h-4 w-4" />
                {updateAgent.isPending ? "Saving..." : "Save Tool Configuration"}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Knowledge Base Tab */}
        <TabsContent value="knowledge">
          <Card>
            <CardHeader>
              <CardTitle>Knowledge Base</CardTitle>
              <CardDescription>
                Upload documents for the agent to reference during interactions.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button variant="outline">
                <Upload className="mr-2 h-4 w-4" />
                Upload Document
              </Button>

              {agent.knowledge_base?.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Document</TableHead>
                      <TableHead>Size</TableHead>
                      <TableHead>Uploaded</TableHead>
                      <TableHead className="w-12" />
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {agent.knowledge_base.map((doc) => (
                      <TableRow key={doc.id}>
                        <TableCell className="font-medium">
                          <div className="flex items-center gap-2">
                            <FileText className="h-4 w-4 text-muted-foreground" />
                            {doc.name}
                          </div>
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {(doc.size / 1024).toFixed(1)} KB
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {new Date(doc.uploaded_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <Button variant="ghost" size="sm">
                            <Trash2 className="h-4 w-4 text-red-400" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <p className="text-sm text-muted-foreground">
                  No documents uploaded yet. Upload a document to enhance agent responses.
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Deployments Tab */}
        <TabsContent value="deployments">
          <Card>
            <CardHeader>
              <CardTitle>Deployments</CardTitle>
              <CardDescription>
                View and manage deployments across environments.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {agent.deployments?.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Environment</TableHead>
                      <TableHead>Version</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Deployed</TableHead>
                      <TableHead className="w-24" />
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {agent.deployments.map((dep) => (
                      <TableRow key={dep.id}>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={envColor[dep.environment] ?? ""}
                          >
                            {dep.environment}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-mono text-sm">{dep.version}</TableCell>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={
                              dep.status === "active"
                                ? "bg-green-500/20 text-green-400 border-green-500/30"
                                : "bg-zinc-500/20 text-zinc-400 border-zinc-500/30"
                            }
                          >
                            {dep.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {new Date(dep.deployed_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => promoteDeployment.mutate(dep.id)}
                            disabled={promoteDeployment.isPending}
                          >
                            <Rocket className="mr-1 h-3 w-3" />
                            Promote
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <p className="text-sm text-muted-foreground">
                  No deployments yet. Deploy this agent to an environment to get started.
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
