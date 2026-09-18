import { notFound } from "next/navigation";
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
      <main className="workspace">
        <p className="error-text">Couldn&apos;t load this scenario: {(err as Error).message}</p>
      </main>
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
