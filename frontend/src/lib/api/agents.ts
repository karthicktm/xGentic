import api from "@/lib/api";

export interface Agent {
  id: string;
  name: string;
  description: string | null;
  agent_type: "voice" | "chat" | "email" | "document_workflow";
  status: "draft" | "active" | "archived";
  system_prompt: string;
  language: string;
  temperature: number;
  max_tokens: number;
  provider_type: string;
  provider_config: Record<string, unknown>;
  type_config: Record<string, unknown>;
  version: number;
  enabled_tools: string[];
  public_id: string | null;
  embed_enabled: boolean;
  total_interactions: number;
  agent_source: "local" | "azure_foundry";
  azure_foundry_agent_id: string | null;
  created_at: string;
  updated_at: string;
}

export async function getAgents(agentType?: string): Promise<Agent[]> {
  const params = agentType ? { agent_type: agentType } : {};
  const res = await api.get("/api/v1/agents", { params });
  return res.data;
}

export async function getAgent(id: string): Promise<Agent> {
  const res = await api.get(`/api/v1/agents/${id}`);
  return res.data;
}

export async function createAgent(data: Partial<Agent>): Promise<Agent> {
  const res = await api.post("/api/v1/agents", data);
  return res.data;
}

export async function updateAgent(id: string, data: Partial<Agent>): Promise<Agent> {
  const res = await api.patch(`/api/v1/agents/${id}`, data);
  return res.data;
}

export async function deleteAgent(id: string): Promise<void> {
  await api.delete(`/api/v1/agents/${id}`);
}

export async function deployAgent(id: string, environmentId: string) {
  const res = await api.post(`/api/v1/agents/${id}/deploy`, {
    environment_id: environmentId,
  });
  return res.data;
}

export async function promoteAgent(
  id: string,
  fromEnvId: string,
  toEnvId: string
) {
  const res = await api.post(`/api/v1/agents/${id}/promote`, {
    from_environment_id: fromEnvId,
    to_environment_id: toEnvId,
  });
  return res.data;
}

export async function getAgentVersions(id: string) {
  const res = await api.get(`/api/v1/agents/${id}/versions`);
  return res.data;
}

// Azure AI Foundry API functions

export interface AzureConnectionStatus {
  connected: boolean;
  provider: string;
  endpoint: string;
  models_available: number;
  error: string | null;
}

export interface AzureModel {
  id: string;
  name: string;
  provider: string;
  capabilities: string[] | null;
}

export interface ImportAzureAgentRequest {
  name: string;
  agent_type?: string;
  system_prompt?: string;
  azure_foundry_agent_id: string;
  azure_endpoint?: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
}

export async function testAzureConnection(
  endpoint?: string,
  apiKey?: string
): Promise<AzureConnectionStatus> {
  const res = await api.post("/api/v1/azure-foundry/test-connection", {
    endpoint,
    api_key: apiKey,
  });
  return res.data;
}

export async function listAzureModels(): Promise<AzureModel[]> {
  const res = await api.get("/api/v1/azure-foundry/models");
  return res.data;
}

export async function importAzureAgent(data: ImportAzureAgentRequest) {
  const res = await api.post("/api/v1/azure-foundry/import-agent", data);
  return res.data;
}

export async function deployToAzure(agentId: string) {
  const res = await api.post(`/api/v1/azure-foundry/deploy/${agentId}`);
  return res.data;
}
