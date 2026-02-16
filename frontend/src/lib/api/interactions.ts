import api from "@/lib/api";

export interface Interaction {
  id: string;
  interaction_type: "voice_call" | "chat_session" | "email_thread" | "document_workflow";
  status: "active" | "completed" | "failed" | "cancelled";
  agent_id: string | null;
  contact_id: number | null;
  workspace_id: string | null;
  environment_id: string | null;
  duration_seconds: number | null;
  token_count: number | null;
  disposition: string | null;
  sentiment: string | null;
  summary: string | null;
  transcript: string | null;
  type_data: Record<string, unknown>;
  created_at: string;
}

export async function getInteractions(params?: {
  interaction_type?: string;
  agent_id?: string;
  workspace_id?: string;
  limit?: number;
  offset?: number;
}): Promise<Interaction[]> {
  const res = await api.get("/api/v1/interactions", { params });
  return res.data;
}

export async function getInteraction(id: string): Promise<Interaction> {
  const res = await api.get(`/api/v1/interactions/${id}`);
  return res.data;
}
