"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Settings, Sun, Moon, Bell, User } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import api from "@/lib/api";

interface UserSettings {
  theme: "light" | "dark" | "system";
  notifications: {
    email_enabled: boolean;
    push_enabled: boolean;
    campaign_updates: boolean;
    agent_alerts: boolean;
    weekly_summary: boolean;
  };
  profile: {
    name: string;
    email: string;
    phone: string;
    timezone: string;
  };
}

export default function SettingsPage() {
  const queryClient = useQueryClient();

  const { data: settings, isLoading } = useQuery<UserSettings>({
    queryKey: ["settings"],
    queryFn: async () => {
      const res = await api.get("/api/v1/settings");
      return res.data;
    },
  });

  const [profile, setProfile] = useState({
    name: "",
    email: "",
    phone: "",
    timezone: "",
  });

  useEffect(() => {
    if (settings?.profile) {
      setProfile(settings.profile);
    }
  }, [settings]);

  const updateSettings = useMutation({
    mutationFn: async (data: Partial<UserSettings>) => {
      const res = await api.patch("/api/v1/settings", data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
  });

  const toggleNotification = (key: keyof UserSettings["notifications"]) => {
    if (settings) {
      updateSettings.mutate({
        notifications: {
          ...settings.notifications,
          [key]: !settings.notifications[key],
        },
      });
    }
  };

  const setTheme = (theme: "light" | "dark" | "system") => {
    updateSettings.mutate({ theme });
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else if (theme === "light") {
      document.documentElement.classList.remove("dark");
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-sm text-muted-foreground">Loading settings...</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Manage your profile, appearance, and notification preferences.
        </p>
      </div>

      {/* Theme */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5 text-primary" />
            Appearance
          </CardTitle>
          <CardDescription>Choose your preferred theme.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            {([
              { value: "light", label: "Light", icon: Sun },
              { value: "dark", label: "Dark", icon: Moon },
              { value: "system", label: "System", icon: Settings },
            ] as const).map((option) => {
              const Icon = option.icon;
              const isActive = settings?.theme === option.value;
              return (
                <Button
                  key={option.value}
                  variant={isActive ? "default" : "outline"}
                  className="flex-1"
                  onClick={() => setTheme(option.value)}
                >
                  <Icon className="mr-2 h-4 w-4" />
                  {option.label}
                </Button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-primary" />
            Notifications
          </CardTitle>
          <CardDescription>Configure how and when you receive notifications.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Email Notifications</Label>
              <p className="text-sm text-muted-foreground">
                Receive notifications via email.
              </p>
            </div>
            <Switch
              checked={settings?.notifications.email_enabled ?? false}
              onCheckedChange={() => toggleNotification("email_enabled")}
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Push Notifications</Label>
              <p className="text-sm text-muted-foreground">
                Receive browser push notifications.
              </p>
            </div>
            <Switch
              checked={settings?.notifications.push_enabled ?? false}
              onCheckedChange={() => toggleNotification("push_enabled")}
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Campaign Updates</Label>
              <p className="text-sm text-muted-foreground">
                Get notified when campaigns start, complete, or fail.
              </p>
            </div>
            <Switch
              checked={settings?.notifications.campaign_updates ?? false}
              onCheckedChange={() => toggleNotification("campaign_updates")}
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Agent Alerts</Label>
              <p className="text-sm text-muted-foreground">
                Get notified about agent errors or status changes.
              </p>
            </div>
            <Switch
              checked={settings?.notifications.agent_alerts ?? false}
              onCheckedChange={() => toggleNotification("agent_alerts")}
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Weekly Summary</Label>
              <p className="text-sm text-muted-foreground">
                Receive a weekly email summary of platform activity.
              </p>
            </div>
            <Switch
              checked={settings?.notifications.weekly_summary ?? false}
              onCheckedChange={() => toggleNotification("weekly_summary")}
            />
          </div>
        </CardContent>
      </Card>

      {/* Profile */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5 text-primary" />
            Profile Information
          </CardTitle>
          <CardDescription>Update your personal profile details.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="profile-name">Name</Label>
            <Input
              id="profile-name"
              value={profile.name}
              onChange={(e) => setProfile({ ...profile, name: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="profile-email">Email</Label>
            <Input
              id="profile-email"
              type="email"
              value={profile.email}
              onChange={(e) => setProfile({ ...profile, email: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="profile-phone">Phone</Label>
            <Input
              id="profile-phone"
              value={profile.phone}
              onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="profile-timezone">Timezone</Label>
            <Input
              id="profile-timezone"
              placeholder="e.g. America/New_York"
              value={profile.timezone}
              onChange={(e) => setProfile({ ...profile, timezone: e.target.value })}
            />
          </div>
          <Button
            onClick={() => updateSettings.mutate({ profile })}
            disabled={updateSettings.isPending}
          >
            {updateSettings.isPending ? "Saving..." : "Save Profile"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
