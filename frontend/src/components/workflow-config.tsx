"use client";

import { Plus, Trash2, GripVertical } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface WorkflowStep {
  name: string;
  action: string;
  description: string;
}

interface WorkflowConfig {
  workflow_steps: WorkflowStep[];
  output_format: string;
}

interface WorkflowConfigProps {
  config: WorkflowConfig;
  onChange: (config: WorkflowConfig) => void;
}

export function WorkflowConfigPanel({ config, onChange }: WorkflowConfigProps) {
  const addStep = () => {
    onChange({
      ...config,
      workflow_steps: [...config.workflow_steps, { name: "", action: "extract", description: "" }],
    });
  };

  const removeStep = (index: number) => {
    onChange({
      ...config,
      workflow_steps: config.workflow_steps.filter((_, i) => i !== index),
    });
  };

  const updateStep = (index: number, partial: Partial<WorkflowStep>) => {
    const steps = [...config.workflow_steps];
    steps[index] = { ...steps[index], ...partial };
    onChange({ ...config, workflow_steps: steps });
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label>Output Format</Label>
        <Select
          value={config.output_format}
          onValueChange={(v) => onChange({ ...config, output_format: v })}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select output format" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="json">JSON</SelectItem>
            <SelectItem value="text">Plain Text</SelectItem>
            <SelectItem value="markdown">Markdown</SelectItem>
            <SelectItem value="html">HTML</SelectItem>
            <SelectItem value="csv">CSV</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label>Workflow Steps</Label>
          <Button variant="outline" size="sm" onClick={addStep}>
            <Plus className="mr-1 h-3 w-3" />
            Add Step
          </Button>
        </div>

        {config.workflow_steps.length === 0 ? (
          <p className="rounded-lg border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
            No workflow steps configured. Add a step to define the document processing pipeline.
          </p>
        ) : (
          <div className="space-y-3">
            {config.workflow_steps.map((step, i) => (
              <div key={i} className="flex items-start gap-2 rounded-lg border border-border p-3">
                <GripVertical className="mt-2 h-4 w-4 shrink-0 text-muted-foreground" />
                <div className="grid flex-1 gap-2 sm:grid-cols-3">
                  <Input
                    placeholder="Step name"
                    value={step.name}
                    onChange={(e) => updateStep(i, { name: e.target.value })}
                  />
                  <Select
                    value={step.action}
                    onValueChange={(v) => updateStep(i, { action: v })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="extract">Extract</SelectItem>
                      <SelectItem value="classify">Classify</SelectItem>
                      <SelectItem value="summarize">Summarize</SelectItem>
                      <SelectItem value="transform">Transform</SelectItem>
                      <SelectItem value="validate">Validate</SelectItem>
                      <SelectItem value="route">Route</SelectItem>
                    </SelectContent>
                  </Select>
                  <Input
                    placeholder="Description"
                    value={step.description}
                    onChange={(e) => updateStep(i, { description: e.target.value })}
                  />
                </div>
                <Button variant="ghost" size="sm" onClick={() => removeStep(i)}>
                  <Trash2 className="h-3 w-3 text-red-400" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
