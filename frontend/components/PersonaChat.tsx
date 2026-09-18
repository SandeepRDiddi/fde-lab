"use client";

import { useState } from "react";
import { AlertCircle, MessageSquare, Send } from "lucide-react";
import type { Message } from "../lib/types";

export default function PersonaChat({
  instanceId,
  studentId,
  initialMessages,
}: {
  instanceId: string;
  studentId: string;
  initialMessages: Message[];
}) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSend() {
    const message = draft.trim();
    if (!message || sending) return;

    setSending(true);
    setError(null);
    const optimisticId = `pending-${Date.now()}`;
    const optimistic: Message = {
      id: optimisticId,
      role: "student",
      content: message,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimistic]);
    setDraft("");

    try {
      const res = await fetch(`/api/scenario-instances/${instanceId}/messages`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ student_id: studentId, message }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? "Failed to send message");
      const reply = (await res.json()) as Message;
      setMessages((prev) => [...prev, reply]);
    } catch (err) {
      // Roll back the optimistic entry -- it was never persisted, so
      // leaving it in place would show a message as sent when it wasn't,
      // and it'd silently vanish on the next real refetch anyway.
      setMessages((prev) => prev.filter((m) => m.id !== optimisticId));
      setDraft(message);
      setError((err as Error).message);
    } finally {
      setSending(false);
    }
  }

  return (
    <section className="card">
      <div className="card-header">
        <MessageSquare size={17} />
        <h2>Persona chat</h2>
      </div>
      <ul className="chat-log">
        {messages.map((message) => (
          <li key={message.id} className={`chat-row from-${message.role}`}>
            <span className={`chat-avatar ${message.role}`}>{message.role === "persona" ? "D" : "Y"}</span>
            <div className="chat-bubble">
              <span className="chat-role">{message.role === "persona" ? "Client" : "You"}</span>
              <p>{message.content}</p>
            </div>
          </li>
        ))}
        {messages.length === 0 && (
          <li className="empty-state">
            <MessageSquare size={14} /> No messages yet — say hello.
          </li>
        )}
      </ul>

      {error && (
        <p className="error-text">
          <AlertCircle size={14} /> {error}
        </p>
      )}

      <div className="chat-input">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            // Skip while an IME composition is in progress -- the Enter that
            // confirms a composed character (e.g. Japanese/Chinese input)
            // would otherwise send the message before composition finishes.
            if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="Message the persona…"
          disabled={sending}
        />
        <button onClick={handleSend} disabled={sending || !draft.trim()}>
          <Send size={14} /> {sending ? "Sending…" : "Send"}
        </button>
      </div>
    </section>
  );
}
