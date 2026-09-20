"use client";

import { useState } from "react";
import {
  AlertCircle,
  Calendar,
  Check,
  FileText,
  RefreshCw,
  Users,
  X,
} from "lucide-react";
import AppShell from "./AppShell";
import ScenarioGenerator from "./ScenarioGenerator";
import type { ApprovalStatus, ScenarioInstance, SubmissionDetail } from "../lib/types";

const STATUS_LABEL: Record<ScenarioInstance["status"], string> = {
  not_started: "Not started",
  active: "Active",
  closed: "Closed",
};

const APPROVAL_LABEL: Record<ApprovalStatus, string> = {
  submitted: "Submitted",
  pending_review: "Pending review",
  approved: "Approved",
  rejected: "Rejected",
};

function toIsoOrNull(datetimeLocalValue: string): string | null {
  return datetimeLocalValue ? new Date(datetimeLocalValue).toISOString() : null;
}

function initials(id: string): string {
  return id.replace(/-/g, "").slice(0, 2).toUpperCase();
}

export default function InstructorConsole({
  cohortId,
  initialInstances,
}: {
  cohortId: string;
  initialInstances: ScenarioInstance[];
}) {
  const [instances, setInstances] = useState<ScenarioInstance[]>(initialInstances);
  const [refreshing, setRefreshing] = useState(false);

  const [startAt, setStartAt] = useState("");
  const [endAt, setEndAt] = useState("");
  const [pivotAt, setPivotAt] = useState("");
  const [scheduling, setScheduling] = useState(false);
  const [scheduleError, setScheduleError] = useState<string | null>(null);

  const [selectedInstanceId, setSelectedInstanceId] = useState<string | null>(null);
  const [submissions, setSubmissions] = useState<SubmissionDetail[]>([]);
  const [loadingSubmissions, setLoadingSubmissions] = useState(false);
  const [submissionsError, setSubmissionsError] = useState<string | null>(null);
  const [decidingId, setDecidingId] = useState<string | null>(null);

  async function refresh() {
    setRefreshing(true);
    try {
      const res = await fetch(`/api/cohorts/${cohortId}/instances`, { cache: "no-store" });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? "Failed to load cohort");
      setInstances((await res.json()) as ScenarioInstance[]);
    } catch (err) {
      setScheduleError((err as Error).message);
    } finally {
      setRefreshing(false);
    }
  }

  // AC1: applies the same start/end/pivot schedule to every student instance
  // currently in this cohort — one screen, one action, whole cohort's run.
  async function applySchedule() {
    const startIso = toIsoOrNull(startAt);
    const endIso = toIsoOrNull(endAt);
    if (!startIso || !endIso) {
      setScheduleError("Start and end time are required");
      return;
    }
    setScheduling(true);
    setScheduleError(null);

    const failures: string[] = [];
    const updated: ScenarioInstance[] = [];
    for (const instance of instances) {
      try {
        const res = await fetch(`/api/scenario-instances/${instance.id}/schedule`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ start_at: startIso, end_at: endIso, pivot_at: toIsoOrNull(pivotAt) }),
        });
        if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? "Schedule failed");
        updated.push((await res.json()) as ScenarioInstance);
      } catch (err) {
        failures.push(`${instance.student_id}: ${(err as Error).message}`);
      }
    }

    setInstances((prev) => prev.map((instance) => updated.find((u) => u.id === instance.id) ?? instance));
    if (failures.length > 0) setScheduleError(failures.join("; "));
    setScheduling(false);
  }

  async function viewSubmissions(instanceId: string) {
    setSelectedInstanceId(instanceId);
    setLoadingSubmissions(true);
    setSubmissionsError(null);
    try {
      const res = await fetch(`/api/scenario-instances/${instanceId}/submissions`, { cache: "no-store" });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? "Failed to load submissions");
      setSubmissions((await res.json()) as SubmissionDetail[]);
    } catch (err) {
      setSubmissionsError((err as Error).message);
      setSubmissions([]);
    } finally {
      setLoadingSubmissions(false);
    }
  }

  async function decide(instanceId: string, submissionId: string, decision: ApprovalStatus) {
    if (decision !== "approved" && decision !== "rejected") return;
    setDecidingId(submissionId);
    try {
      const res = await fetch(`/api/scenario-instances/${instanceId}/submissions/${submissionId}/decision`, {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ decision }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? "Decision failed");
      const decided = (await res.json()) as SubmissionDetail;
      setSubmissions((prev) => prev.map((s) => (s.id === decided.id ? decided : s)));
      await refresh();
    } catch (err) {
      setSubmissionsError((err as Error).message);
    } finally {
      setDecidingId(null);
    }
  }

  return (
    <AppShell role="Instructor">
      <main className="page">
        <div className="page-header">
          <span className="page-eyebrow">Cohort {cohortId.slice(0, 8)}</span>
          <h1>Cohort console</h1>
          <p className="page-subtitle">Schedule this cohort&apos;s scenario and review student progress.</p>
        </div>

        <ScenarioGenerator cohortId={cohortId} onCreated={refresh} />

        <section className="card">
          <div className="card-header">
            <Calendar size={17} />
            <h2>Schedule this cohort&apos;s scenario</h2>
          </div>
          <div className="schedule-form">
            <label>
              Start
              <input type="datetime-local" value={startAt} onChange={(e) => setStartAt(e.target.value)} />
            </label>
            <label>
              End
              <input type="datetime-local" value={endAt} onChange={(e) => setEndAt(e.target.value)} />
            </label>
            <label>
              Pivot (optional)
              <input type="datetime-local" value={pivotAt} onChange={(e) => setPivotAt(e.target.value)} />
            </label>
            <button onClick={applySchedule} disabled={scheduling || instances.length === 0}>
              {scheduling ? "Applying…" : "Apply to cohort"}
            </button>
          </div>
          {instances.length === 0 && <p className="empty-state">No students in this cohort yet.</p>}
          {scheduleError && (
            <p className="error-text">
              <AlertCircle size={14} /> {scheduleError}
            </p>
          )}
        </section>

        <section className="card">
          <div className="card-header" style={{ justifyContent: "space-between" }}>
            <span style={{ display: "flex", alignItems: "center", gap: "0.55rem" }}>
              <Users size={17} />
              <h2>Students</h2>
            </span>
            <button className="btn-secondary" onClick={refresh} disabled={refreshing}>
              <RefreshCw size={13} /> {refreshing ? "Refreshing…" : "Refresh"}
            </button>
          </div>
          {instances.length === 0 ? (
            <p className="empty-state">No students in this cohort yet.</p>
          ) : (
            <div className="table-scroll">
              <table className="roster-table">
                <thead>
                  <tr>
                    <th>Student</th>
                    <th>Status</th>
                    <th>Approval outcome</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {instances.map((instance) => (
                    <tr key={instance.id}>
                      <td>
                        <div className="roster-student">
                          <span className="roster-avatar">{initials(instance.student_id)}</span>
                          <span className="roster-id">{instance.student_id}</span>
                        </div>
                      </td>
                      <td>
                        <span className={`status-pill status-${instance.status}`}>{STATUS_LABEL[instance.status]}</span>
                      </td>
                      <td>
                        {instance.approval_outcome ? (
                          <span className={`approval-badge approval-${instance.approval_outcome}`}>
                            {APPROVAL_LABEL[instance.approval_outcome]}
                          </span>
                        ) : (
                          <span className="empty-state">—</span>
                        )}
                      </td>
                      <td>
                        <button className="btn-secondary" onClick={() => viewSubmissions(instance.id)}>
                          <FileText size={13} /> View submission
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {selectedInstanceId && (
          <section className="card">
            <div className="card-header">
              <FileText size={17} />
              <h2>
                Submission — student{" "}
                {instances.find((i) => i.id === selectedInstanceId)?.student_id}
              </h2>
            </div>
            {loadingSubmissions && <p className="empty-state">Loading…</p>}
            {submissionsError && (
              <p className="error-text">
                <AlertCircle size={14} /> {submissionsError}
              </p>
            )}
            {!loadingSubmissions && submissions.length === 0 && (
              <p className="empty-state">This student hasn&apos;t submitted anything yet.</p>
            )}
            {submissions.map((submission) => (
              <div key={submission.id} className="submission-detail">
                <p className="submission-status">
                  Status:{" "}
                  <span className={`approval-badge approval-${submission.status}`}>
                    {APPROVAL_LABEL[submission.status]}
                  </span>
                </p>
                <p className="empty-state">
                  {submission.grading_result
                    ? `Auto-graded (${submission.grading_result.task_type}): correct — a technical task submission is only recorded once it's actually run and checked, not just compliance-gated.`
                    : "Compliance: passed — submissions are only recorded once they clear the compliance checklist."}
                </p>
                <pre className="submission-content">{submission.content}</pre>
                {submission.status === "pending_review" && (
                  <div className="chat-input">
                    <button
                      onClick={() => decide(selectedInstanceId, submission.id, "approved")}
                      disabled={decidingId === submission.id}
                    >
                      <Check size={14} /> Approve
                    </button>
                    <button
                      className="btn-secondary"
                      onClick={() => decide(selectedInstanceId, submission.id, "rejected")}
                      disabled={decidingId === submission.id}
                    >
                      <X size={14} /> Reject
                    </button>
                  </div>
                )}
              </div>
            ))}
          </section>
        )}
      </main>
    </AppShell>
  );
}
