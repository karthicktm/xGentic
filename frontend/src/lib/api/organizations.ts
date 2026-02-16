import api from "@/lib/api";

export interface Organization {
  id: string;
  name: string;
  slug: string;
  owner_id: number;
  sso_provider: string | null;
  azure_tenant_id: string | null;
  max_users: number;
  max_agents: number;
  features_enabled: string[];
  is_active: boolean;
  created_at: string;
}

export interface HierarchyNode {
  id: string;
  name: string;
  slug: string;
  type: string;
  units?: HierarchyNode[];
  departments?: HierarchyNode[];
  projects?: HierarchyNode[];
  workspaces?: HierarchyNode[];
  is_default?: boolean;
}

export async function getOrganizations(): Promise<Organization[]> {
  const res = await api.get("/api/v1/organizations");
  return res.data;
}

export async function getOrganization(id: string): Promise<Organization> {
  const res = await api.get(`/api/v1/organizations/${id}`);
  return res.data;
}

export async function getHierarchyTree(): Promise<HierarchyNode[]> {
  const res = await api.get("/api/v1/hierarchy/tree");
  return res.data;
}

export async function getUnits(orgId: string) {
  const res = await api.get(`/api/v1/organizations/${orgId}/units`);
  return res.data;
}

export async function getDepartments(unitId: string) {
  const res = await api.get(`/api/v1/units/${unitId}/departments`);
  return res.data;
}

export async function getProjects(deptId: string) {
  const res = await api.get(`/api/v1/departments/${deptId}/projects`);
  return res.data;
}

export async function getWorkspaces(projectId: string) {
  const res = await api.get(`/api/v1/projects/${projectId}/workspaces`);
  return res.data;
}
