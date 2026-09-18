import type { ConversationRead, Message, ScenarioInstance, SubmissionRecord } from "./types";

// Server-side only — these route to the scenario engine (backend/) and the AI
// persona service (persona-service/) directly. Kept out of NEXT_PUBLIC_* so
// browser code can never see or hit them directly; client components always
// go through this app's own /api/* route handlers instead, which avoids
// needing CORS configured on either FastAPI service.
const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";
const PERSONA_SERVICE_URL = process.env.PERSONA_SERVICE_URL ?? "http://localhost:8001";

export class UpstreamError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function asJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new UpstreamError(res.status, body || res.statusText);
  }
  return res.json() as Promise<T>;
}

export async function getScenarioInstance(instanceId: string): Promise<ScenarioInstance> {
  const res = await fetch(`${BACKEND_URL}/scenario-instances/${instanceId}`, { cache: "no-store" });
  return asJson<ScenarioInstance>(res);
}

export async function getConversation(instanceId: string, studentId: string): Promise<ConversationRead> {
  const res = await fetch(
    `${PERSONA_SERVICE_URL}/scenario-instances/${instanceId}/messages?student_id=${studentId}`,
    { cache: "no-store" }
  );
  return asJson<ConversationRead>(res);
}

export async function sendMessage(instanceId: string, studentId: string, message: string): Promise<Message> {
  const res = await fetch(`${PERSONA_SERVICE_URL}/scenario-instances/${instanceId}/messages`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ student_id: studentId, message }),
  });
  return asJson<Message>(res);
}

/**
 * Records a submission that already passed the local compliance check
 * (lib/compliance.ts) against the backend's approval workflow (FDE-007).
 * Only `content` is accepted by the backend's SubmissionCreate schema — a
 * submission belongs to one scenario instance, which is already scoped to
 * one student, so there's no separate student_id to send.
 */
export async function submitToBackend(instanceId: string, content: string): Promise<SubmissionRecord> {
  const res = await fetch(`${BACKEND_URL}/scenario-instances/${instanceId}/submissions`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ content }),
  });
  return asJson<SubmissionRecord>(res);
}
