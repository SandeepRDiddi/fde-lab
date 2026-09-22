import { AlertCircle } from "lucide-react";
import { notFound } from "next/navigation";
import AppShell from "../../../components/AppShell";
import { getConversation, getEngagement, UpstreamError } from "../../../lib/backend";
import type { Message } from "../../../lib/types";
import EngagementClient from "./EngagementClient";

export default async function EngagementPage({
  params,
  searchParams,
}: {
  params: { engagementId: string };
  searchParams: { stage?: string };
}) {
  let engagement;
  try {
    engagement = await getEngagement(params.engagementId);
  } catch (err) {
    if (err instanceof UpstreamError && err.status === 404) notFound();
    return (
      <AppShell role="Student">
        <main className="page">
          <p className="error-text">
            <AlertCircle size={14} /> Couldn&apos;t load this engagement: {(err as Error).message}
          </p>
        </main>
      </AppShell>
    );
  }

  // The frontier stage: the highest-order stage that isn't locked
  // (not_started). Every approved stage stays "active" too (FDE-017 never
  // closes a prior stage), so this is the last non-locked one, not the
  // first "active" one.
  const unlockedStages = engagement.stages.filter((s) => s.status !== "not_started");
  const frontier = unlockedStages[unlockedStages.length - 1] ?? engagement.stages[0];

  const requestedOrder = searchParams.stage !== undefined ? Number(searchParams.stage) : null;
  const requested =
    requestedOrder !== null ? engagement.stages.find((s) => s.stage_order === requestedOrder) : undefined;
  const focused = requested && requested.status !== "not_started" ? requested : frontier;

  let initialMessages: Message[] = [];
  if (focused.status === "active") {
    try {
      const conversation = await getConversation(focused.id, engagement.student_id);
      initialMessages = conversation.messages;
    } catch {
      // Persona service unreachable -- chat opens empty rather than blocking
      // the rest of the page from rendering.
      initialMessages = [];
    }
  }

  return <EngagementClient engagement={engagement} focusedStageOrder={focused.stage_order!} initialMessages={initialMessages} />;
}
