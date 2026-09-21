"use client";

import { useMemo, useState } from "react";
import CodeMirror from "@uiw/react-codemirror";
import { sql } from "@codemirror/lang-sql";
import { python } from "@codemirror/lang-python";
import { AlertCircle, CheckCircle2, FileCheck2, Play, XCircle } from "lucide-react";
import type { QueryRunResult, SubmissionResult, TechnicalTask } from "../lib/types";

function defaultInstructions(task: TechnicalTask): string {
  if (task.task_type === "python_script") {
    return `Write a Python script that reads "${task.input_filename}" and writes "${task.output_filename}". It's graded by running it, not by what it says.`;
  }
  return `Write a read-only SQL query against the "${task.table_name}" table. It's graded by running it, not by what it says.`;
}

function placeholderFor(task: TechnicalTask): string {
  if (task.task_type === "python_script") {
    return `# read ${task.input_filename}, write ${task.output_filename}\nimport json\n`;
  }
  return `SELECT ... FROM ${task.table_name} ...`;
}

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

  const [running, setRunning] = useState(false);
  const [runResult, setRunResult] = useState<QueryRunResult | null>(null);
  const [runError, setRunError] = useState<string | null>(null);

  const editorExtensions = useMemo(
    () => [technicalTask?.task_type === "python_script" ? python() : sql()],
    [technicalTask?.task_type]
  );

  async function handleRun() {
    if (!content.trim() || running) return;
    setRunning(true);
    setRunError(null);
    setRunResult(null);
    try {
      const res = await fetch(`/api/scenario-instances/${instanceId}/technical-task/run`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ content }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? "Run failed");
      setRunResult((await res.json()) as QueryRunResult);
    } catch (err) {
      setRunError((err as Error).message);
    } finally {
      setRunning(false);
    }
  }

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
        <h2>{technicalTask ? (technicalTask.task_type === "python_script" ? "Write your script" : "Write your query") : "Submit your work"}</h2>
      </div>
      {!canSubmit && <p className="empty-state">This scenario isn&apos;t active — submissions are closed.</p>}

      {technicalTask && (
        <p className="empty-state" style={{ marginBottom: "0.75rem" }}>
          {technicalTask.instructions ?? defaultInstructions(technicalTask)}
        </p>
      )}

      {technicalTask ? (
        <div className="code-editor">
          <CodeMirror
            value={content}
            onChange={setContent}
            extensions={editorExtensions}
            editable={canSubmit && !submitting && !running}
            placeholder={placeholderFor(technicalTask)}
            height="200px"
            basicSetup={{ lineNumbers: true, foldGutter: false }}
          />
        </div>
      ) : (
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Paste or write your deliverable…"
          disabled={!canSubmit || submitting}
          rows={6}
        />
      )}

      <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.6rem" }}>
        {technicalTask && (
          <button
            className="btn-secondary"
            onClick={handleRun}
            disabled={!canSubmit || running || submitting || !content.trim()}
          >
            <Play size={14} /> {running ? "Running…" : "Run"}
          </button>
        )}
        <button onClick={handleSubmit} disabled={!canSubmit || submitting || running || !content.trim()}>
          {submitting ? "Grading…" : technicalTask ? "Submit" : "Submit for compliance review"}
        </button>
      </div>

      {runError && (
        <p className="error-text">
          <AlertCircle size={14} /> {runError}
        </p>
      )}

      {runResult && (
        <div className="run-result-table">
          <p className="run-result-caption">
            {runResult.row_count} row{runResult.row_count === 1 ? "" : "s"} returned
            {runResult.truncated && ` (showing first ${runResult.rows.length})`} — not graded, this is just a
            preview.
          </p>
          <div className="table-scroll">
            <table className="roster-table">
              <thead>
                <tr>
                  {runResult.columns.map((col) => (
                    <th key={col}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {runResult.rows.map((row, i) => (
                  <tr key={i}>
                    {row.map((value, j) => (
                      <td key={j} style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>
                        {value === null ? (
                          <span className="empty-state" style={{ display: "inline" }}>
                            null
                          </span>
                        ) : (
                          String(value)
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

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
                {technicalTask ? "Graded correct." : "All compliance checks passed."}
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
