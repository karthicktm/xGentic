"use client";

import { useState } from "react";
import { ArrowRight, Loader2, Rocket } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { EnvBadge } from "@/components/env-badge";

interface Environment {
  id: string;
  name: string;
  type: string;
}

interface PromotionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agentName: string;
  currentEnvironment: Environment;
  availableEnvironments: Environment[];
  onPromote: (targetEnvironmentId: string) => Promise<void>;
}

export function PromotionDialog({
  open,
  onOpenChange,
  agentName,
  currentEnvironment,
  availableEnvironments,
  onPromote,
}: PromotionDialogProps) {
  const [targetId, setTargetId] = useState<string>("");
  const [promoting, setPromoting] = useState(false);

  const targets = availableEnvironments.filter((e) => e.id !== currentEnvironment.id);
  const targetEnv = targets.find((e) => e.id === targetId);

  const handlePromote = async () => {
    if (!targetId) return;
    setPromoting(true);
    try {
      await onPromote(targetId);
      onOpenChange(false);
    } finally {
      setPromoting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Rocket className="h-5 w-5 text-primary" />
            Promote Agent
          </DialogTitle>
          <DialogDescription>
            Promote <strong>{agentName}</strong> from one environment to another. This will copy the
            current deployment configuration.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="flex items-center justify-center gap-4">
            <div className="text-center">
              <Label className="text-xs text-muted-foreground">From</Label>
              <div className="mt-1">
                <EnvBadge environment={currentEnvironment.type} />
              </div>
            </div>
            <ArrowRight className="h-5 w-5 text-muted-foreground" />
            <div className="text-center">
              <Label className="text-xs text-muted-foreground">To</Label>
              <div className="mt-1">
                {targetEnv ? (
                  <EnvBadge environment={targetEnv.type} />
                ) : (
                  <span className="text-xs text-muted-foreground">Select target</span>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Target Environment</Label>
            <Select value={targetId} onValueChange={setTargetId}>
              <SelectTrigger>
                <SelectValue placeholder="Select environment" />
              </SelectTrigger>
              <SelectContent>
                {targets.map((env) => (
                  <SelectItem key={env.id} value={env.id}>
                    {env.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handlePromote} disabled={!targetId || promoting}>
            {promoting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Promoting...
              </>
            ) : (
              <>
                <Rocket className="mr-2 h-4 w-4" />
                Promote
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
