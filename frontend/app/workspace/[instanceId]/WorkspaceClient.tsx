"use client";

import ArtifactFeed from "../../../components/ArtifactFeed";
import DatasetLink from "../../../components/DatasetLink";
import PersonaChat from "../../../components/PersonaChat";
import ScenarioStatusHeader from "../../../components/ScenarioStatusHeader";
import SubmissionPanel from "../../../components/SubmissionPanel";
import type { Message, ScenarioInstance } from "../../../lib/types";

export default function WorkspaceClient({
  instance,
  initialMessages,
}: {
  instance: ScenarioInstance;
  initialMessages: Message[];
}) {
  const isActive = instance.status === "active";

  return (
    <main className="workspace">
      <ScenarioStatusHeader instance={instance} />

      {isActive && (
        <div className="workspace-grid">
          <PersonaChat instanceId={instance.id} studentId={instance.student_id} initialMessages={initialMessages} />
          <div className="workspace-sidebar">
            <ArtifactFeed artifacts={instance.config.artifacts ?? []} />
            <DatasetLink location={instance.dataset_location} />
          </div>
        </div>
      )}

      <SubmissionPanel instanceId={instance.id} studentId={instance.student_id} canSubmit={isActive} />
    </main>
  );
}
