"use client";

import { useState } from "react";
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
    const optimistic: Message = {
      id: `pending-${Date.now()}`,
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
      setError((err as Error).message);
    } finally {
      setSending(false);
    }
  }

  return (
    <section className="panel">
      <h2>Persona chat</h2>
      <ul className="chat-log">
        {messages.map((message) => (
          <li key={message.id} className={`chat-message chat-${message.role}`}>
            <span className="chat-role">{message.role === "persona" ? "Client" : "You"}</span>
            <p>{message.content}</p>
          </li>
        ))}
        {messages.length === 0 && <li className="empty-state">No messages yet — say hello.</li>}
      </ul>

      {error && <p className="error-text">{error}</p>}

      <div className="chat-input">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="Message the persona…"
          disabled={sending}
        />
        <button onClick={handleSend} disabled={sending || !draft.trim()}>
          {sending ? "Sending…" : "Send"}
        </button>
      </div>
    </section>
  );
}
