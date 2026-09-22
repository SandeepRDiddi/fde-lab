"use client";

import { CheckCircle2, Lock, MessageCircleQuestion, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import AppShell from "../../../components/AppShell";
import ArtifactFeed from "../../../components/ArtifactFeed";
import DatasetPreview from "../../../components/DatasetPreview";
import LegacySystemPanel from "../../../components/LegacySystemPanel";
import PersonaChat from "../../../components/PersonaChat";
import ScenarioStatusHeader from "../../../components/ScenarioStatusHeader";
import SubmissionPanel from "../../../components/SubmissionPanel";
import type { Engagement, Message, ScenarioInstance } from "../../../lib/types";

type StageDisplayStatus = "locked" | "active" | "approved" | "rejected";

// A prior stage stays instance-status "active" forever once unlocked
// (FDE-017 never closes it) -- approval_outcome, not instance.status, is
// what actually distinguishes "currently open" from "already done".
function displayStatus(stage: ScenarioInstance): StageDisplayStatus {
  if (stage.status === "not_started") return "locked";
  if (stage.approval_outcome === "approved") return "approved";
  if (stage.approval_outcome === "rejected") return "rejected";
  return "active";
}

const STATUS_META: Record<StageDisplayStatus, { label: string; icon: typeof Lock }> = {
  locked: { label: "Locked", icon: Lock },
  active: { label: "Active", icon: MessageCircleQuestion },
  approved: { label: "Approved", icon: CheckCircle2 },
  rejected: { label: "Needs resubmission", icon: MessageCircleQuestion },
};

export default function EngagementClient({
  engagement,
  focusedStageOrder,
  initialMessages,
}: {
  engagement: Engagement;
  focusedStageOrder: number;
  initialMessages: Message[];
}) {
  const router = useRouter();
  const [refreshing, setRefreshing] = useState(false);
  const focused = engagement.stages.find((s) => s.stage_order === focusedStageOrder) ?? engagement.stages[0];
  const isActive = focused.status === "active";

  function refresh() {
    setRefreshing(true);
    router.refresh();
    // No promise from router.refresh() to await -- just give the spinner a
    // moment so a fast refresh doesn't look like it did nothing.
    setTimeout(() => setRefreshing(false), 500);
  }

  return (
    <AppShell role="Student">
      <main className="page">
        <div className="page-header">
          <span className="page-eyebrow">Engagement {engagement.id.slice(0, 8)}</span>
          <h1>Your engagement</h1>
          {engagement.status === "completed" && (
            <p className="page-subtitle">
              <CheckCircle2 size={14} /> All stages complete — this engagement is finished.
            </p>
          )}
        </div>

        <div className="workspace-grid">
          <section className="card" style={{ minWidth: "220px" }}>
            <div className="card-header" style={{ justifyContent: "space-between" }}>
              <h2>Stages</h2>
              <button className="btn-secondary" onClick={refresh} disabled={refreshing}>
                <RefreshCw size={13} /> {refreshing ? "…" : "Refresh"}
              </button>
            </div>
            <ul className="chat-log" style={{ gap: "0.3rem" }}>
              {engagement.stages.map((stage) => {
                const status = displayStatus(stage);
                const meta = STATUS_META[status];
                const Icon = meta.icon;
                const isFocused = stage.stage_order === focusedStageOrder;
                const content = (
                  <>
                    <span className={`status-pill status-${status === "locked" ? "not_started" : "active"}`}>
                      <Icon size={12} /> Stage {stage.stage_order}
                    </span>
                    <span className="empty-state" style={{ marginLeft: "0.5rem" }}>
                      {meta.label}
                    </span>
                  </>
                );
                return (
                  <li key={stage.id} className={`chat-row ${isFocused ? "from-persona" : ""}`}>
                    {status === "locked" ? (
                      <span className="empty-state">{content}</span>
                    ) : (
                      <Link href={`/engagement/${engagement.id}?stage=${stage.stage_order}`}>{content}</Link>
                    )}
                  </li>
                );
              })}
            </ul>
          </section>

          <div>
            <ScenarioStatusHeader instance={focused} />

            {isActive && (
              <div className="workspace-grid">
                <PersonaChat instanceId={focused.id} studentId={engagement.student_id} initialMessages={initialMessages} />
                <div className="workspace-sidebar">
                  <ArtifactFeed artifacts={focused.config.artifacts ?? []} />
                  <LegacySystemPanel instanceId={focused.id} legacySystem={focused.config.legacy_system} />
                  <DatasetPreview instanceId={focused.id} hasDataset={Boolean(focused.dataset_location)} />
                </div>
              </div>
            )}

            <SubmissionPanel
              instanceId={focused.id}
              studentId={engagement.student_id}
              canSubmit={isActive}
              technicalTask={focused.config.technical_task}
            />
          </div>
        </div>
      </main>
    </AppShell>
  );
}
