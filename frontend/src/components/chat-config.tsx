"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";

interface ChatConfig {
  welcome_message: string;
  typing_indicator: boolean;
  max_history: number;
}

interface ChatConfigProps {
  config: ChatConfig;
  onChange: (config: ChatConfig) => void;
}

export function ChatConfigPanel({ config, onChange }: ChatConfigProps) {
  const update = (partial: Partial<ChatConfig>) => onChange({ ...config, ...partial });

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label>Welcome Message</Label>
        <Textarea
          value={config.welcome_message}
          onChange={(e) => update({ welcome_message: e.target.value })}
          placeholder="Hi! I'm here to help. What can I do for you?"
          rows={3}
        />
      </div>

      <div className="space-y-2">
        <Label>Max Conversation History</Label>
        <Input
          type="number"
          value={config.max_history}
          onChange={(e) => update({ max_history: parseInt(e.target.value) || 50 })}
          min={10}
          max={500}
        />
        <p className="text-xs text-muted-foreground">
          Maximum number of messages to retain in conversation context.
        </p>
      </div>

      <div className="flex items-center justify-between rounded-lg border border-border p-3">
        <div>
          <Label>Typing Indicator</Label>
          <p className="text-xs text-muted-foreground">
            Show a typing animation while the agent is thinking
          </p>
        </div>
        <Switch
          checked={config.typing_indicator}
          onCheckedChange={(v) => update({ typing_indicator: v })}
        />
      </div>
    </div>
  );
}
