"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Cloud, Plus } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
import api from "@/lib/api";

interface Environment {
  id: string;
  name: string;
  environment_type: string;
  provider: string;
  status: string;
  deployed_agent_count: number;
  created_at: string;
}

const typeColor: Record<string, string> = {
  development: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  dev: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  qa: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  staging: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  production: "bg-green-500/20 text-green-400 border-green-500/30",
};

const statusColor: Record<string, string> = {
  healthy: "bg-green-500/20 text-green-400 border-green-500/30",
  active: "bg-green-500/20 text-green-400 border-green-500/30",
  degraded: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  down: "bg-red-500/20 text-red-400 border-red-500/30",
  provisioning: "bg-blue-500/20 text-blue-400 border-blue-500/30",
};

export default function EnvironmentsPage() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({
    name: "",
    environment_type: "",
    provider: "",
  });

  const { data: environments = [], isLoading } = useQuery<Environment[]>({
    queryKey: ["environments"],
    queryFn: async () => {
      const res = await api.get("/api/v1/environments");
      return res.data;
    },
  });

  const createEnvironment = useMutation({
    mutationFn: async (data: { name: string; environment_type: string; provider: string }) => {
      const res = await api.post("/api/v1/environments", data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["environments"] });
      setDialogOpen(false);
      setForm({ name: "", environment_type: "", provider: "" });
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Environments</h1>
          <p className="text-sm text-muted-foreground">
            Manage deployment environments across your infrastructure.
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create Environment
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Environment</DialogTitle>
              <DialogDescription>
                Set up a new deployment environment.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="env-name">Name</Label>
                <Input
                  id="env-name"
                  placeholder="e.g. Production US-East"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Type</Label>
                <Select
                  value={form.environment_type}
                  onValueChange={(val) => setForm({ ...form, environment_type: val })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select environment type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="development">Development</SelectItem>
                    <SelectItem value="qa">QA</SelectItem>
                    <SelectItem value="staging">Staging</SelectItem>
                    <SelectItem value="production">Production</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Provider</Label>
                <Select
                  value={form.provider}
                  onValueChange={(val) => setForm({ ...form, provider: val })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select provider" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="aws">AWS</SelectItem>
                    <SelectItem value="gcp">GCP</SelectItem>
                    <SelectItem value="azure">Azure</SelectItem>
                    <SelectItem value="on-premise">On-Premise</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={() => createEnvironment.mutate(form)}
                disabled={
                  !form.name.trim() ||
                  !form.environment_type ||
                  !form.provider ||
                  createEnvironment.isPending
                }
              >
                {createEnvironment.isPending ? "Creating..." : "Create"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cloud className="h-5 w-5 text-primary" />
            All Environments
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading environments...</p>
          ) : environments.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No environments found. Create an environment to get started.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Provider</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Deployed Agents</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {environments.map((env) => (
                  <TableRow key={env.id}>
                    <TableCell className="font-medium">{env.name}</TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={typeColor[env.environment_type] ?? ""}
                      >
                        {env.environment_type}
                      </Badge>
                    </TableCell>
                    <TableCell className="uppercase text-muted-foreground">
                      {env.provider}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={statusColor[env.status] ?? ""}>
                        {env.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {env.deployed_agent_count ?? 0}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
