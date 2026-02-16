"use client";

import { useState } from "react";
import { Copy, Check, Code2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";

interface EmbedAgentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agentName: string;
  publicId: string;
  agentType: string;
  allowedDomains: string[];
}

export function EmbedAgentDialog({
  open,
  onOpenChange,
  agentName,
  publicId,
  agentType,
  allowedDomains,
}: EmbedAgentDialogProps) {
  const [copied, setCopied] = useState<string | null>(null);
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";

  const iframeCode = `<iframe
  src="${baseUrl}/embed/${publicId}"
  width="400"
  height="600"
  style="border: none; border-radius: 12px;"
  allow="microphone"
  title="${agentName}"
></iframe>`;

  const scriptCode = `<script>
  (function() {
    var d = document.createElement('div');
    d.id = 'xgentic-widget';
    document.body.appendChild(d);
    var s = document.createElement('script');
    s.src = '${baseUrl}/embed/widget.js';
    s.setAttribute('data-agent-id', '${publicId}');
    s.setAttribute('data-position', 'bottom-right');
    s.async = true;
    document.head.appendChild(s);
  })();
</script>`;

  const directUrl = `${baseUrl}/embed/${publicId}`;

  const copyToClipboard = async (text: string, key: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Code2 className="h-5 w-5 text-primary" />
            Embed {agentName}
          </DialogTitle>
          <DialogDescription>
            Embed this {agentType} agent on your internal portals or intranet.
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="iframe" className="mt-4">
          <TabsList className="w-full">
            <TabsTrigger value="iframe" className="flex-1">
              iFrame
            </TabsTrigger>
            <TabsTrigger value="script" className="flex-1">
              Script Tag
            </TabsTrigger>
            <TabsTrigger value="url" className="flex-1">
              Direct URL
            </TabsTrigger>
          </TabsList>

          <TabsContent value="iframe" className="space-y-3">
            <div className="relative">
              <pre className="rounded-lg border border-border bg-card p-3 text-xs overflow-x-auto">
                {iframeCode}
              </pre>
              <Button
                variant="ghost"
                size="sm"
                className="absolute right-2 top-2"
                onClick={() => copyToClipboard(iframeCode, "iframe")}
              >
                {copied === "iframe" ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="script" className="space-y-3">
            <div className="relative">
              <pre className="rounded-lg border border-border bg-card p-3 text-xs overflow-x-auto">
                {scriptCode}
              </pre>
              <Button
                variant="ghost"
                size="sm"
                className="absolute right-2 top-2"
                onClick={() => copyToClipboard(scriptCode, "script")}
              >
                {copied === "script" ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="url" className="space-y-3">
            <div className="flex gap-2">
              <Input value={directUrl} readOnly className="font-mono text-xs" />
              <Button variant="outline" size="sm" onClick={() => copyToClipboard(directUrl, "url")}>
                {copied === "url" ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
              </Button>
            </div>
          </TabsContent>
        </Tabs>

        {allowedDomains.length > 0 && (
          <div className="mt-4 space-y-2">
            <Label className="text-xs text-muted-foreground">Allowed Domains</Label>
            <div className="flex flex-wrap gap-1">
              {allowedDomains.map((domain) => (
                <Badge key={domain} variant="secondary" className="text-xs">
                  {domain}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
