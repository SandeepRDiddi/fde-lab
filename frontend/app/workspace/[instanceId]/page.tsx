import { AlertCircle } from "lucide-react";
import { notFound } from "next/navigation";
import AppShell from "../../../components/AppShell";
import { getConversation, getScenarioInstance, UpstreamError } from "../../../lib/backend";
import type { Message } from "../../../lib/types";
import WorkspaceClient from "./WorkspaceClient";

export default async function WorkspacePage({ params }: { params: { instanceId: string } }) {
  let instance;
  try {
    instance = await getScenarioInstance(params.instanceId);
  } catch (err) {
    if (err instanceof UpstreamError && err.status === 404) notFound();
    return (
      <AppShell role="Student">
        <main className="page">
          <p className="error-text">
            <AlertCircle size={14} /> Couldn&apos;t load this scenario: {(err as Error).message}
          </p>
        </main>
      </AppShell>
    );
  }

  let initialMessages: Message[] = [];
  if (instance.status === "active") {
    try {
      const conversation = await getConversation(instance.id, instance.student_id);
      initialMessages = conversation.messages;
    } catch {
      // Persona service unreachable — chat opens empty rather than blocking the
      // rest of the workspace from rendering.
      initialMessages = [];
    }
  }

  return <WorkspaceClient instance={instance} initialMessages={initialMessages} />;
}
