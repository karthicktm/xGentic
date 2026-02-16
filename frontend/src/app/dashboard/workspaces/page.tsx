"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Users, Plus, UserPlus, Trash2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import api from "@/lib/api";
import { useHierarchyStore } from "@/lib/hierarchy-store";

interface Project {
  id: string;
  name: string;
}

interface WorkspaceMember {
  id: string;
  name: string;
  email: string;
  role: string;
  joined_at: string;
}

interface Workspace {
  id: string;
  name: string;
  slug: string;
  description: string;
  status: string;
  member_count: number;
  members: WorkspaceMember[];
  created_at: string;
}

const statusColor: Record<string, string> = {
  active: "bg-green-500/20 text-green-400 border-green-500/30",
  inactive: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30",
  archived: "bg-red-500/20 text-red-400 border-red-500/30",
};

const roleColor: Record<string, string> = {
  owner: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  admin: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  member: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30",
  viewer: "bg-amber-500/20 text-amber-400 border-amber-500/30",
};

export default function WorkspacesPage() {
  const queryClient = useQueryClient();
  const { projectId, projectName, setWorkspace } = useHierarchyStore();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [memberDialogOpen, setMemberDialogOpen] = useState(false);
  const [selectedWorkspace, setSelectedWorkspace] = useState<Workspace | null>(null);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [form, setForm] = useState({ name: "", slug: "", description: "" });
  const [memberEmail, setMemberEmail] = useState("");

  const { data: projects = [] } = useQuery<Project[]>({
    queryKey: ["projects"],
    queryFn: async () => {
      const res = await api.get("/api/v1/projects");
      return res.data;
    },
  });

  const { data: workspaces = [], isLoading } = useQuery<Workspace[]>({
    queryKey: ["workspaces"],
    queryFn: async () => {
      const res = await api.get("/api/v1/workspaces");
      return res.data;
    },
  });

  const createWorkspace = useMutation({
    mutationFn: async (data: { name: string; slug: string; description: string }) => {
      const useProjectId = selectedProjectId || projectId;
      if (!useProjectId) throw new Error("Please select a project");
      const res = await api.post(`/api/v1/projects/${useProjectId}/workspaces`, data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
      setDialogOpen(false);
      setForm({ name: "", slug: "", description: "" });
      setSelectedProjectId("");
    },
  });

  const addMember = useMutation({
    mutationFn: async ({ workspaceId, email }: { workspaceId: string; email: string }) => {
      const res = await api.post(`/api/v1/workspaces/${workspaceId}/members`, { email });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
      setMemberEmail("");
    },
  });

  const removeMember = useMutation({
    mutationFn: async ({ workspaceId, memberId }: { workspaceId: string; memberId: string }) => {
      await api.delete(`/api/v1/workspaces/${workspaceId}/members/${memberId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Workspaces</h1>
          <p className="text-sm text-muted-foreground">
            Manage workspaces and team members within {projectName ?? "this project"}.
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create Workspace
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Workspace</DialogTitle>
              <DialogDescription>
                Add a new workspace to {projectName ?? "this project"}.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="project-select">Project</Label>
                <Select value={selectedProjectId} onValueChange={setSelectedProjectId}>
                  <SelectTrigger id="project-select">
                    <SelectValue placeholder={projectName || "Select a project"} />
                  </SelectTrigger>
                  <SelectContent>
                    {projects.map((proj) => (
                      <SelectItem key={proj.id} value={proj.id}>
                        {proj.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="ws-name">Name</Label>
                <Input
                  id="ws-name"
                  placeholder="e.g. Development Workspace"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="ws-slug">Slug</Label>
                <Input
                  id="ws-slug"
                  placeholder="e.g. dev-workspace"
                  value={form.slug}
                  onChange={(e) => setForm({ ...form, slug: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="ws-description">Description</Label>
                <Input
                  id="ws-description"
                  placeholder="Brief description of this workspace"
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={() => createWorkspace.mutate(form)}
                disabled={!form.name.trim() || createWorkspace.isPending || (!selectedProjectId && !projectId)}
              >
                {createWorkspace.isPending ? "Creating..." : "Create"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5 text-primary" />
            All Workspaces
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading workspaces...</p>
          ) : workspaces.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No workspaces found. Create a workspace to get started.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Slug</TableHead>
                  <TableHead>Members</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-24" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {workspaces.map((ws) => (
                  <TableRow
                    key={ws.id}
                    className="cursor-pointer"
                    onClick={() => setWorkspace(ws.id, ws.name)}
                  >
                    <TableCell className="font-medium">{ws.name}</TableCell>
                    <TableCell className="font-mono text-sm text-muted-foreground">
                      {ws.slug}
                    </TableCell>
                    <TableCell>{ws.member_count ?? 0}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className={statusColor[ws.status] ?? ""}>
                        {ws.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedWorkspace(ws);
                          setMemberDialogOpen(true);
                        }}
                      >
                        <UserPlus className="mr-1 h-3 w-3" />
                        Members
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Member Management Dialog */}
      <Dialog open={memberDialogOpen} onOpenChange={setMemberDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Manage Members - {selectedWorkspace?.name}</DialogTitle>
            <DialogDescription>
              Add or remove workspace members.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="flex gap-2">
              <Input
                placeholder="Enter email address"
                value={memberEmail}
                onChange={(e) => setMemberEmail(e.target.value)}
              />
              <Button
                onClick={() => {
                  if (selectedWorkspace && memberEmail.trim()) {
                    addMember.mutate({
                      workspaceId: selectedWorkspace.id,
                      email: memberEmail,
                    });
                  }
                }}
                disabled={!memberEmail.trim() || addMember.isPending}
              >
                <UserPlus className="mr-1 h-4 w-4" />
                Add
              </Button>
            </div>

            {selectedWorkspace?.members?.length ? (
              <div className="space-y-2">
                {selectedWorkspace.members.map((member) => (
                  <div
                    key={member.id}
                    className="flex items-center justify-between rounded-lg border border-border p-3"
                  >
                    <div>
                      <p className="text-sm font-medium">{member.name}</p>
                      <p className="text-xs text-muted-foreground">{member.email}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className={roleColor[member.role] ?? ""}>
                        {member.role}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          removeMember.mutate({
                            workspaceId: selectedWorkspace.id,
                            memberId: member.id,
                          })
                        }
                      >
                        <Trash2 className="h-3 w-3 text-red-400" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No members yet.</p>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
