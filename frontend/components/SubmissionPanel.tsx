"use client";

import { useState } from "react";
import { AlertCircle, CheckCircle2, FileCheck2, XCircle } from "lucide-react";
import type { SubmissionResult, TechnicalTask } from "../lib/types";

export default function SubmissionPanel({
  instanceId,
  studentId,
  canSubmit,
  technicalTask,
}: {
  instanceId: string;
  studentId: string;
  canSubmit: boolean;
  technicalTask?: TechnicalTask;
}) {
  const [content, setContent] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<SubmissionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    if (!content.trim() || submitting) return;
    setSubmitting(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`/api/scenario-instances/${instanceId}/submit`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ student_id: studentId, content }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? "Submission failed");
      setResult((await res.json()) as SubmissionResult);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="card">
      <div className="card-header">
        <FileCheck2 size={17} />
        <h2>{technicalTask ? "Submit your query" : "Submit your work"}</h2>
      </div>
      {!canSubmit && <p className="empty-state">This scenario isn&apos;t active — submissions are closed.</p>}

      {technicalTask && (
        <p className="empty-state" style={{ marginBottom: "0.75rem" }}>
          {technicalTask.instructions ??
            `Write a read-only SQL query against the "${technicalTask.table_name}" table. It's graded by running it, not by what it says.`}
        </p>
      )}

      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder={technicalTask ? `SELECT ... FROM ${technicalTask.table_name} ...` : "Paste or write your deliverable…"}
        disabled={!canSubmit || submitting}
        rows={6}
        style={technicalTask ? { fontFamily: "var(--font-mono)" } : undefined}
      />
      <div style={{ marginTop: "0.75rem" }}>
        <button onClick={handleSubmit} disabled={!canSubmit || submitting || !content.trim()}>
          {submitting ? "Grading…" : technicalTask ? "Submit query" : "Submit for compliance review"}
        </button>
      </div>

      {error && (
        <p className="error-text">
          <AlertCircle size={14} /> {error}
        </p>
      )}

      {result && (
        <div className={`submission-result ${result.passed ? "passed" : "failed"}`}>
          {result.passed ? (
            <>
              <div className="submission-result-head">
                <CheckCircle2 size={16} />
                {technicalTask ? "Query graded correct." : "All compliance checks passed."}
              </div>
              {result.submission && (
                <p className="submission-status">
                  Status: {result.submission.status}
                  {result.submission.review_deadline_at && (
                    <> — decision expected by {new Date(result.submission.review_deadline_at).toLocaleString()}</>
                  )}
                </p>
              )}
            </>
          ) : (
            <>
              <div className="submission-result-head">
                <XCircle size={16} /> {technicalTask ? "Grading failed" : "Compliance failures"}
              </div>
              <ul>
                {result.failures.map((failure) => (
                  <li key={failure.rule_id}>{failure.description}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </section>
  );
}
