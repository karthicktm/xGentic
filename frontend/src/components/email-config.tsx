"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

interface EmailConfig {
  reply_template: string;
  signature: string;
  max_reply_length: number;
}

interface EmailConfigProps {
  config: EmailConfig;
  onChange: (config: EmailConfig) => void;
}

export function EmailConfigPanel({ config, onChange }: EmailConfigProps) {
  const update = (partial: Partial<EmailConfig>) => onChange({ ...config, ...partial });

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label>Reply Template</Label>
        <Textarea
          value={config.reply_template}
          onChange={(e) => update({ reply_template: e.target.value })}
          placeholder="Use {greeting}, {body}, {signature} placeholders..."
          rows={4}
        />
        <p className="text-xs text-muted-foreground">
          Template for email replies. Use placeholders for dynamic content.
        </p>
      </div>

      <div className="space-y-2">
        <Label>Email Signature</Label>
        <Textarea
          value={config.signature}
          onChange={(e) => update({ signature: e.target.value })}
          placeholder="Best regards,&#10;AI Assistant&#10;Company Name"
          rows={3}
        />
      </div>

      <div className="space-y-2">
        <Label>Max Reply Length (characters)</Label>
        <Input
          type="number"
          value={config.max_reply_length}
          onChange={(e) => update({ max_reply_length: parseInt(e.target.value) || 2000 })}
          min={100}
          max={10000}
        />
      </div>
    </div>
  );
}
