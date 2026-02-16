"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Bot, Mic, MicOff, Send, Loader2 } from "lucide-react";

interface AgentConfig {
  id: string;
  name: string;
  agent_type: "voice" | "chat" | "email" | "document_workflow";
  embed_settings: {
    theme: string;
    position: string;
    primary_color: string;
    greeting_message: string;
    button_text: string;
  };
}

type WidgetState = "idle" | "listening" | "thinking" | "speaking" | "typing" | "responding";

export default function EmbedPage() {
  const params = useParams();
  const publicId = params.publicId as string;
  const [agent, setAgent] = useState<AgentConfig | null>(null);
  const [state, setState] = useState<WidgetState>("idle");
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${apiUrl}/api/v1/embed/${publicId}`)
      .then((res) => res.json())
      .then((data) => {
        setAgent(data);
        if (data.embed_settings?.greeting_message) {
          setMessages([{ role: "assistant", content: data.embed_settings.greeting_message }]);
        }
      })
      .catch(() => setError("Failed to load agent configuration"));
  }, [publicId]);

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setState("thinking");

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/v1/embed/${publicId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage, history: messages }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "assistant", content: data.response }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I encountered an error. Please try again." },
      ]);
    } finally {
      setState("idle");
    }
  };

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#0f172a] text-white">
        <p>{error}</p>
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#0f172a]">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-400" />
      </div>
    );
  }

  // Render based on agent type
  if (agent.agent_type === "voice") {
    return (
      <div className="flex h-screen flex-col items-center justify-center bg-[#0f172a] text-white">
        <div className="mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-indigo-500/20">
          <Bot className="h-12 w-12 text-indigo-400" />
        </div>
        <h2 className="mb-2 text-lg font-semibold">{agent.name}</h2>
        <p className="mb-8 text-sm text-gray-400">Voice Agent</p>
        <button
          onClick={() => setState(state === "listening" ? "idle" : "listening")}
          className={`flex h-16 w-16 items-center justify-center rounded-full transition-colors ${
            state === "listening"
              ? "bg-red-500 hover:bg-red-600"
              : "bg-indigo-500 hover:bg-indigo-600"
          }`}
        >
          {state === "listening" ? (
            <MicOff className="h-6 w-6 text-white" />
          ) : (
            <Mic className="h-6 w-6 text-white" />
          )}
        </button>
        <p className="mt-4 text-xs text-gray-500">
          {state === "listening" ? "Listening..." : "Click to start"}
        </p>
      </div>
    );
  }

  // Chat interface (default for chat/email/document agents)
  return (
    <div className="flex h-screen flex-col bg-[#0f172a]">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-gray-800 px-4 py-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-500/20">
          <Bot className="h-4 w-4 text-indigo-400" />
        </div>
        <div>
          <p className="text-sm font-medium text-white">{agent.name}</p>
          <p className="text-[10px] text-gray-500 capitalize">{agent.agent_type} Agent</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
                msg.role === "user"
                  ? "bg-indigo-500 text-white"
                  : "bg-gray-800 text-gray-200"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {state === "thinking" && (
          <div className="flex justify-start">
            <div className="rounded-lg bg-gray-800 px-3 py-2">
              <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-800 p-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") void handleSendMessage();
            }}
            placeholder="Type a message..."
            className="flex-1 rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
          />
          <button
            onClick={() => void handleSendMessage()}
            disabled={!input.trim() || state === "thinking"}
            className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-500 text-white disabled:opacity-50"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
