"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ShieldCheck, Download, Trash2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import api from "@/lib/api";

interface PrivacySettings {
  data_collection_enabled: boolean;
  analytics_enabled: boolean;
  third_party_sharing_enabled: boolean;
  recording_enabled: boolean;
  transcript_storage_enabled: boolean;
  retention_days: number;
}

export default function CompliancePage() {
  const queryClient = useQueryClient();

  const { data: settings, isLoading } = useQuery<PrivacySettings>({
    queryKey: ["compliance-privacy"],
    queryFn: async () => {
      const res = await api.get("/api/v1/compliance/privacy-settings");
      return res.data;
    },
  });

  const updateSettings = useMutation({
    mutationFn: async (data: Partial<PrivacySettings>) => {
      const res = await api.patch("/api/v1/compliance/privacy-settings", data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["compliance-privacy"] });
    },
  });

  const exportData = useMutation({
    mutationFn: async () => {
      const res = await api.post("/api/v1/compliance/export-data");
      return res.data;
    },
  });

  const deleteData = useMutation({
    mutationFn: async () => {
      const res = await api.post("/api/v1/compliance/delete-data");
      return res.data;
    },
  });

  const toggleSetting = (key: keyof PrivacySettings) => {
    if (settings) {
      updateSettings.mutate({ [key]: !settings[key] });
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Compliance</h1>
        <p className="text-sm text-muted-foreground">Loading settings...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Compliance</h1>
        <p className="text-sm text-muted-foreground">
          Manage privacy settings, data exports, and data deletion for compliance.
        </p>
      </div>

      {/* Privacy Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-primary" />
            Privacy Settings
          </CardTitle>
          <CardDescription>
            Control how data is collected, stored, and shared across the platform.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Data Collection</Label>
              <p className="text-sm text-muted-foreground">
                Allow collection of interaction data for analytics and improvements.
              </p>
            </div>
            <Switch
              checked={settings?.data_collection_enabled ?? false}
              onCheckedChange={() => toggleSetting("data_collection_enabled")}
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Analytics</Label>
              <p className="text-sm text-muted-foreground">
                Enable usage analytics and reporting dashboards.
              </p>
            </div>
            <Switch
              checked={settings?.analytics_enabled ?? false}
              onCheckedChange={() => toggleSetting("analytics_enabled")}
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Third-Party Sharing</Label>
              <p className="text-sm text-muted-foreground">
                Allow sharing anonymized data with third-party integration providers.
              </p>
            </div>
            <Switch
              checked={settings?.third_party_sharing_enabled ?? false}
              onCheckedChange={() => toggleSetting("third_party_sharing_enabled")}
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Call Recording</Label>
              <p className="text-sm text-muted-foreground">
                Record voice interactions for quality assurance and compliance.
              </p>
            </div>
            <Switch
              checked={settings?.recording_enabled ?? false}
              onCheckedChange={() => toggleSetting("recording_enabled")}
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Transcript Storage</Label>
              <p className="text-sm text-muted-foreground">
                Store interaction transcripts for review and training purposes.
              </p>
            </div>
            <Switch
              checked={settings?.transcript_storage_enabled ?? false}
              onCheckedChange={() => toggleSetting("transcript_storage_enabled")}
            />
          </div>
        </CardContent>
      </Card>

      {/* Data Management */}
      <Card>
        <CardHeader>
          <CardTitle>Data Management</CardTitle>
          <CardDescription>
            Export or delete your data in compliance with data privacy regulations.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between rounded-lg border border-border p-4">
            <div>
              <p className="text-sm font-medium">Export Data</p>
              <p className="text-sm text-muted-foreground">
                Download a copy of all your platform data in a portable format.
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => exportData.mutate()}
              disabled={exportData.isPending}
            >
              <Download className="mr-2 h-4 w-4" />
              {exportData.isPending ? "Exporting..." : "Export"}
            </Button>
          </div>

          <div className="flex items-center justify-between rounded-lg border border-red-500/20 p-4">
            <div>
              <p className="text-sm font-medium text-red-400">Delete All Data</p>
              <p className="text-sm text-muted-foreground">
                Permanently delete all your platform data. This action cannot be undone.
              </p>
            </div>
            <Button
              variant="outline"
              className="border-red-500/30 text-red-400 hover:bg-red-500/10"
              onClick={() => {
                if (
                  window.confirm(
                    "Are you sure you want to delete all your data? This action cannot be undone."
                  )
                ) {
                  deleteData.mutate();
                }
              }}
              disabled={deleteData.isPending}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              {deleteData.isPending ? "Deleting..." : "Delete"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
