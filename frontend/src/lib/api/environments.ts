import api from "@/lib/api";

export interface Environment {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
  type: "development" | "qa" | "staging" | "production" | "sandbox";
  provider: string;
  azure_endpoint: string | null;
  azure_resource_group: string | null;
  azure_project_name: string | null;
  provider_config: Record<string, unknown>;
  resource_quotas: Record<string, unknown>;
  is_active: boolean;
  is_locked: boolean;
  created_at: string;
}

export async function getEnvironments(): Promise<Environment[]> {
  const res = await api.get("/api/v1/environments");
  return res.data;
}

export async function getEnvironment(id: string): Promise<Environment> {
  const res = await api.get(`/api/v1/environments/${id}`);
  return res.data;
}

export async function createEnvironment(data: Partial<Environment>): Promise<Environment> {
  const res = await api.post("/api/v1/environments", data);
  return res.data;
}

export async function updateEnvironment(
  id: string,
  data: Partial<Environment>
): Promise<Environment> {
  const res = await api.patch(`/api/v1/environments/${id}`, data);
  return res.data;
}

export async function testEnvironmentConnection(id: string) {
  const res = await api.post(`/api/v1/environments/${id}/test-connection`);
  return res.data;
}
