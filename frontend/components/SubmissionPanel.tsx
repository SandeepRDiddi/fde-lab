"use client";

import { useState } from "react";
import type { SubmissionResult } from "../lib/types";

export default function SubmissionPanel({
  instanceId,
  studentId,
  canSubmit,
}: {
  instanceId: string;
  studentId: string;
  canSubmit: boolean;
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
    <section className="panel">
      <h2>Submit your work</h2>
      {!canSubmit && <p className="empty-state">This scenario isn&apos;t active — submissions are closed.</p>}

      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Paste or write your deliverable…"
        disabled={!canSubmit || submitting}
        rows={6}
      />
      <button onClick={handleSubmit} disabled={!canSubmit || submitting || !content.trim()}>
        {submitting ? "Checking…" : "Submit for compliance review"}
      </button>

      {error && <p className="error-text">{error}</p>}

      {result && (
        <div className={`submission-result ${result.passed ? "passed" : "failed"}`}>
          {result.passed ? (
            <p>All compliance checks passed.</p>
          ) : (
            <>
              <p>Compliance failures:</p>
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
