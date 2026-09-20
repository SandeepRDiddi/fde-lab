"use client";

import AppShell from "../../../components/AppShell";
import ArtifactFeed from "../../../components/ArtifactFeed";
import DatasetLink from "../../../components/DatasetLink";
import LegacySystemPanel from "../../../components/LegacySystemPanel";
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
    <AppShell role="Student">
      <main className="page">
        <div className="page-header">
          <span className="page-eyebrow">Scenario engagement</span>
          <h1>Your workspace</h1>
        </div>

        <ScenarioStatusHeader instance={instance} />

        {isActive && (
          <div className="workspace-grid">
            <PersonaChat instanceId={instance.id} studentId={instance.student_id} initialMessages={initialMessages} />
            <div className="workspace-sidebar">
              <ArtifactFeed artifacts={instance.config.artifacts ?? []} />
              <LegacySystemPanel instanceId={instance.id} legacySystem={instance.config.legacy_system} />
              <DatasetLink location={instance.dataset_location} />
            </div>
          </div>
        )}

        <SubmissionPanel
          instanceId={instance.id}
          studentId={instance.student_id}
          canSubmit={isActive}
          technicalTask={instance.config.technical_task}
        />
      </main>
    </AppShell>
  );
}
