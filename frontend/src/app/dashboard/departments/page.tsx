"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { FolderTree, Plus } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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

interface Unit {
  id: string;
  name: string;
}

interface Department {
  id: string;
  name: string;
  slug: string;
  description: string;
  status: string;
  created_at: string;
}

const statusColor: Record<string, string> = {
  active: "bg-green-500/20 text-green-400 border-green-500/30",
  inactive: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30",
  archived: "bg-red-500/20 text-red-400 border-red-500/30",
};

export default function DepartmentsPage() {
  const queryClient = useQueryClient();
  const { unitId, unitName, setDepartment } = useHierarchyStore();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedUnitId, setSelectedUnitId] = useState<string>("");
  const [form, setForm] = useState({ name: "", slug: "", description: "" });

  const { data: units = [] } = useQuery<Unit[]>({
    queryKey: ["units"],
    queryFn: async () => {
      const res = await api.get("/api/v1/units");
      return res.data;
    },
  });

  const { data: departments = [], isLoading } = useQuery<Department[]>({
    queryKey: ["departments"],
    queryFn: async () => {
      const res = await api.get("/api/v1/departments");
      return res.data;
    },
  });

  const createDepartment = useMutation({
    mutationFn: async (data: { name: string; slug: string; description: string }) => {
      const useUnitId = selectedUnitId || unitId;
      if (!useUnitId) throw new Error("Please select a unit");
      const res = await api.post(`/api/v1/units/${useUnitId}/departments`, data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["departments"] });
      setDialogOpen(false);
      setForm({ name: "", slug: "", description: "" });
      setSelectedUnitId("");
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Departments</h1>
          <p className="text-sm text-muted-foreground">
            Manage departments within {unitName ?? "this unit"}.
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create Department
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Department</DialogTitle>
              <DialogDescription>
                Add a new department to {unitName ?? "this unit"}.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="unit-select">Unit</Label>
                <Select value={selectedUnitId} onValueChange={setSelectedUnitId}>
                  <SelectTrigger id="unit-select">
                    <SelectValue placeholder={unitName || "Select a unit"} />
                  </SelectTrigger>
                  <SelectContent>
                    {units.map((unit) => (
                      <SelectItem key={unit.id} value={unit.id}>
                        {unit.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="dept-name">Name</Label>
                <Input
                  id="dept-name"
                  placeholder="e.g. Backend Team"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="dept-slug">Slug</Label>
                <Input
                  id="dept-slug"
                  placeholder="e.g. backend-team"
                  value={form.slug}
                  onChange={(e) => setForm({ ...form, slug: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="dept-description">Description</Label>
                <Input
                  id="dept-description"
                  placeholder="Brief description of this department"
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
                onClick={() => createDepartment.mutate(form)}
                disabled={!form.name.trim() || createDepartment.isPending || (!selectedUnitId && !unitId)}
              >
                {createDepartment.isPending ? "Creating..." : "Create"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FolderTree className="h-5 w-5 text-primary" />
            All Departments
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading departments...</p>
          ) : departments.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No departments found. Create a department to get started.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Slug</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {departments.map((dept) => (
                  <TableRow
                    key={dept.id}
                    className="cursor-pointer"
                    onClick={() => setDepartment(dept.id, dept.name)}
                  >
                    <TableCell className="font-medium">{dept.name}</TableCell>
                    <TableCell className="font-mono text-sm text-muted-foreground">
                      {dept.slug}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {dept.description || "---"}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={statusColor[dept.status] ?? ""}>
                        {dept.status}
                      </Badge>
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
