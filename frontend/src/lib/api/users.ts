import api from "@/lib/api";

export interface UserInfo {
  id: number;
  email: string;
  full_name: string | null;
  role: string;
  department: string | null;
  job_title: string | null;
  is_active: boolean;
  last_login_at: string | null;
}

export async function getUsers(): Promise<UserInfo[]> {
  const res = await api.get("/api/v1/users");
  return res.data;
}

export async function updateUser(id: number, data: Partial<UserInfo>): Promise<UserInfo> {
  const res = await api.patch(`/api/v1/users/${id}`, data);
  return res.data;
}

export async function deleteUser(id: number): Promise<void> {
  await api.delete(`/api/v1/users/${id}`);
}
