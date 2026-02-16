"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import {
  Phone,
  MessageSquare,
  Mail,
  GitBranch,
  ArrowLeft,
  ArrowRight,
  Check,
  Cloud,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import api from "@/lib/api";

const agentTypeOptions = [
  {
    type: "voice",
    label: "Voice Agent",
    description: "Real-time voice conversations via phone or web.",
    icon: Phone,
    color: "text-blue-400 border-blue-500/30 hover:border-blue-500/60",
  },
  {
    type: "chat",
    label: "Chat Agent",
    description: "Text-based chat interactions on web or messaging platforms.",
    icon: MessageSquare,
    color: "text-purple-400 border-purple-500/30 hover:border-purple-500/60",
  },
  {
    type: "email",
    label: "Email Agent",
    description: "Automated email response and triage workflows.",
    icon: Mail,
    color: "text-amber-400 border-amber-500/30 hover:border-amber-500/60",
  },
  {
    type: "workflow",
    label: "Workflow Agent",
    description: "Document processing and multi-step automation pipelines.",
    icon: GitBranch,
    color: "text-green-400 border-green-500/30 hover:border-green-500/60",
  },
];

const providerOptions = [
  {
    id: "azure_foundry",
    label: "Azure AI Foundry",
    description: "Enterprise-grade Azure AI models with DefaultAzureCredential.",
    icon: Cloud,
  },
];

const azureModels = [
  { id: "gpt-4o", label: "GPT-4o", description: "Most capable, best for complex tasks" },
  { id: "gpt-4o-mini", label: "GPT-4o Mini", description: "Fast and cost-effective" },
];

interface AgentForm {
  name: string;
  description: string;
  agent_type: string;
  system_prompt: string;
  temperature: number;
  max_tokens: number;
  provider_type: string;
  provider_config: {
    azure_endpoint?: string;
    model?: string;
  };
}

export default function NewAgentPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<AgentForm>({
    name: "",
    description: "",
    agent_type: "",
    system_prompt: "",
    temperature: 0.7,
    max_tokens: 4096,
    provider_type: "azure_foundry",
    provider_config: {
      model: "gpt-4o",
    },
  });

  const createAgent = useMutation({
    mutationFn: async (data: AgentForm) => {
      const res = await api.post("/api/v1/agents", data);
      return res.data;
    },
    onSuccess: (data) => {
      router.push(`/dashboard/agents/${data.id}`);
    },
  });

  const canProceed =
    step === 0
      ? form.agent_type !== ""
      : step === 1
        ? form.name.trim() !== ""
        : true;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.push("/dashboard/agents")}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Create New Agent</h1>
          <p className="text-sm text-muted-foreground">
            Step {step + 1} of 3 &mdash;{" "}
            {step === 0
              ? "Choose agent type"
              : step === 1
                ? "Configure your agent"
                : "Provider settings"}
          </p>
        </div>
      </div>

      {/* Step indicators */}
      <div className="flex items-center gap-2">
        {[0, 1, 2].map((s) => (
          <div
            key={s}
            className={`h-1.5 flex-1 rounded-full transition-colors ${
              s <= step ? "bg-primary" : "bg-muted"
            }`}
          />
        ))}
      </div>

      {/* Step 0: Type Selection */}
      {step === 0 && (
        <div className="grid gap-4 sm:grid-cols-2">
          {agentTypeOptions.map((option) => {
            const Icon = option.icon;
            const isSelected = form.agent_type === option.type;
            return (
              <Card
                key={option.type}
                className={`cursor-pointer transition-all ${option.color} ${
                  isSelected ? "ring-2 ring-primary" : ""
                }`}
                onClick={() => setForm({ ...form, agent_type: option.type })}
              >
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Icon className={`h-5 w-5 ${option.color.split(" ")[0]}`} />
                    {option.label}
                  </CardTitle>
                  <CardDescription>{option.description}</CardDescription>
                </CardHeader>
                {isSelected && (
                  <CardContent>
                    <div className="flex items-center gap-1 text-sm text-primary">
                      <Check className="h-4 w-4" />
                      Selected
                    </div>
                  </CardContent>
                )}
              </Card>
            );
          })}
        </div>
      )}

      {/* Step 1: Configuration */}
      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Agent Configuration</CardTitle>
            <CardDescription>
              Configure the details for your{" "}
              {agentTypeOptions.find((o) => o.type === form.agent_type)?.label ?? "agent"}.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                placeholder="e.g. Customer Support Agent"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Input
                id="description"
                placeholder="Brief description of what this agent does"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="system_prompt">System Prompt</Label>
              <Textarea
                id="system_prompt"
                placeholder="You are a helpful assistant that..."
                rows={6}
                value={form.system_prompt}
                onChange={(e) => setForm({ ...form, system_prompt: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label>Temperature: {form.temperature.toFixed(2)}</Label>
              <Slider
                min={0}
                max={2}
                step={0.01}
                value={[form.temperature]}
                onValueChange={([val]) => setForm({ ...form, temperature: val })}
              />
              <p className="text-xs text-muted-foreground">
                Lower values produce more focused output. Higher values increase creativity.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="max_tokens">Max Tokens</Label>
              <Input
                id="max_tokens"
                type="number"
                min={256}
                max={128000}
                value={form.max_tokens}
                onChange={(e) =>
                  setForm({ ...form, max_tokens: parseInt(e.target.value) || 4096 })
                }
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Provider Settings */}
      {step === 2 && (
        <Card>
          <CardHeader>
            <CardTitle>Provider Settings</CardTitle>
            <CardDescription>
              Configure the AI provider for your agent. Azure AI Foundry uses
              DefaultAzureCredential for authentication.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Provider selection */}
            <div className="space-y-3">
              <Label>Provider</Label>
              {providerOptions.map((provider) => {
                const isSelected = form.provider_type === provider.id;
                return (
                  <Card
                    key={provider.id}
                    className={`cursor-pointer transition-all ${
                      isSelected
                        ? "border-primary ring-2 ring-primary"
                        : "border-border hover:border-primary/50"
                    }`}
                    onClick={() => setForm({ ...form, provider_type: provider.id })}
                  >
                    <CardHeader className="py-4">
                      <CardTitle className="flex items-center gap-2 text-base">
                        <provider.icon className="h-5 w-5 text-blue-400" />
                        {provider.label}
                        {isSelected && <Check className="ml-auto h-4 w-4 text-primary" />}
                      </CardTitle>
                      <CardDescription className="text-xs">
                        {provider.description}
                      </CardDescription>
                    </CardHeader>
                  </Card>
                );
              })}
            </div>

            {/* Azure-specific fields */}
            {form.provider_type === "azure_foundry" && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="azure_model">Model</Label>
                  <Select
                    value={form.provider_config.model ?? "gpt-4o"}
                    onValueChange={(value) =>
                      setForm({
                        ...form,
                        provider_config: { ...form.provider_config, model: value },
                      })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select model" />
                    </SelectTrigger>
                    <SelectContent>
                      {azureModels.map((model) => (
                        <SelectItem key={model.id} value={model.id}>
                          <div>
                            <span className="font-medium">{model.label}</span>
                            <span className="ml-2 text-xs text-muted-foreground">
                              {model.description}
                            </span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="azure_endpoint">
                    Azure Endpoint{" "}
                    <span className="text-xs text-muted-foreground">(optional override)</span>
                  </Label>
                  <Input
                    id="azure_endpoint"
                    placeholder="https://your-resource.openai.azure.com"
                    value={form.provider_config.azure_endpoint ?? ""}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        provider_config: {
                          ...form.provider_config,
                          azure_endpoint: e.target.value || undefined,
                        },
                      })
                    }
                  />
                  <p className="text-xs text-muted-foreground">
                    Leave empty to use the default endpoint from server configuration.
                    Authentication uses DefaultAzureCredential automatically.
                  </p>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      )}

      {/* Navigation */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={() => setStep(Math.max(0, step - 1))}
          disabled={step === 0}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>

        {step < 2 ? (
          <Button onClick={() => setStep(step + 1)} disabled={!canProceed}>
            Next
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        ) : (
          <Button
            onClick={() => createAgent.mutate(form)}
            disabled={!canProceed || createAgent.isPending}
          >
            {createAgent.isPending ? "Creating..." : "Create Agent"}
            <Check className="ml-2 h-4 w-4" />
          </Button>
        )}
      </div>

      {createAgent.isError && (
        <p className="text-sm text-red-400">
          Failed to create agent. Please try again.
        </p>
      )}
    </div>
  );
}
