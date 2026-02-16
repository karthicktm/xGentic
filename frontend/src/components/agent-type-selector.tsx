"use client";

import { Bot, MessageSquare, Mail, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

const agentTypes = [
  {
    value: "voice",
    label: "Voice Agent",
    description: "Handle phone calls with AI-powered voice interactions",
    icon: Bot,
    color: "text-blue-400 border-blue-500/30 bg-blue-500/10",
    selectedColor: "border-blue-500 bg-blue-500/20",
  },
  {
    value: "chat",
    label: "Chat Agent",
    description: "Real-time chat support for web and internal portals",
    icon: MessageSquare,
    color: "text-green-400 border-green-500/30 bg-green-500/10",
    selectedColor: "border-green-500 bg-green-500/20",
  },
  {
    value: "email",
    label: "Email Agent",
    description: "Automated email responses and thread management",
    icon: Mail,
    color: "text-amber-400 border-amber-500/30 bg-amber-500/10",
    selectedColor: "border-amber-500 bg-amber-500/20",
  },
  {
    value: "document_workflow",
    label: "Document / Workflow",
    description: "Document processing and workflow automation",
    icon: FileText,
    color: "text-purple-400 border-purple-500/30 bg-purple-500/10",
    selectedColor: "border-purple-500 bg-purple-500/20",
  },
] as const;

export type AgentTypeValue = (typeof agentTypes)[number]["value"];

interface AgentTypeSelectorProps {
  value: AgentTypeValue | null;
  onChange: (value: AgentTypeValue) => void;
}

export function AgentTypeSelector({ value, onChange }: AgentTypeSelectorProps) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {agentTypes.map((type) => {
        const Icon = type.icon;
        const isSelected = value === type.value;
        return (
          <button
            key={type.value}
            type="button"
            onClick={() => onChange(type.value)}
            className={cn(
              "flex items-start gap-3 rounded-lg border p-4 text-left transition-all hover:border-primary/50",
              isSelected ? type.selectedColor : "border-border bg-card",
            )}
          >
            <div className={cn("mt-0.5 rounded-md p-2", type.color)}>
              <Icon className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-medium">{type.label}</p>
              <p className="mt-1 text-xs text-muted-foreground">{type.description}</p>
            </div>
          </button>
        );
      })}
    </div>
  );
}
