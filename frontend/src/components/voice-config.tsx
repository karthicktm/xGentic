"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface VoiceConfig {
  voice: string;
  turn_detection_mode: string;
  threshold: number;
  padding: number;
  silence: number;
  initial_greeting: string;
  enable_recording: boolean;
}

interface VoiceConfigProps {
  config: VoiceConfig;
  onChange: (config: VoiceConfig) => void;
}

export function VoiceConfigPanel({ config, onChange }: VoiceConfigProps) {
  const update = (partial: Partial<VoiceConfig>) => onChange({ ...config, ...partial });

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Voice</Label>
          <Select value={config.voice} onValueChange={(v) => update({ voice: v })}>
            <SelectTrigger>
              <SelectValue placeholder="Select voice" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="alloy">Alloy</SelectItem>
              <SelectItem value="echo">Echo</SelectItem>
              <SelectItem value="fable">Fable</SelectItem>
              <SelectItem value="onyx">Onyx</SelectItem>
              <SelectItem value="nova">Nova</SelectItem>
              <SelectItem value="shimmer">Shimmer</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Turn Detection Mode</Label>
          <Select
            value={config.turn_detection_mode}
            onValueChange={(v) => update({ turn_detection_mode: v })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select mode" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="server_vad">Server VAD</SelectItem>
              <SelectItem value="semantic_vad">Semantic VAD</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-2">
        <Label>VAD Threshold ({config.threshold})</Label>
        <Slider
          value={[config.threshold]}
          min={0}
          max={1}
          step={0.05}
          onValueChange={([v]) => update({ threshold: v })}
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Silence Duration (ms)</Label>
          <Input
            type="number"
            value={config.silence}
            onChange={(e) => update({ silence: parseInt(e.target.value) || 0 })}
          />
        </div>
        <div className="space-y-2">
          <Label>Padding (ms)</Label>
          <Input
            type="number"
            value={config.padding}
            onChange={(e) => update({ padding: parseInt(e.target.value) || 0 })}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label>Initial Greeting</Label>
        <Textarea
          value={config.initial_greeting}
          onChange={(e) => update({ initial_greeting: e.target.value })}
          placeholder="Hello! How can I help you today?"
          rows={3}
        />
      </div>

      <div className="flex items-center justify-between rounded-lg border border-border p-3">
        <div>
          <Label>Enable Recording</Label>
          <p className="text-xs text-muted-foreground">Record calls for review and compliance</p>
        </div>
        <Switch
          checked={config.enable_recording}
          onCheckedChange={(v) => update({ enable_recording: v })}
        />
      </div>
    </div>
  );
}
