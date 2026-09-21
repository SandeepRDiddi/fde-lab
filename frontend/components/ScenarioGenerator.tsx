"use client";

import { useState } from "react";
import { AlertCircle, CheckCircle2, Sparkles } from "lucide-react";
import type { GeneratedScenarioConfig, ScenarioInstance } from "../lib/types";

function randomId(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export default function ScenarioGenerator({
  cohortId,
  onCreated,
}: {
  cohortId: string;
  onCreated: () => void;
}) {
  const [requirement, setRequirement] = useState("");
  const [generating, setGenerating] = useState(false);
  const [draft, setDraft] = useState<GeneratedScenarioConfig | null>(null);
  const [studentId, setStudentId] = useState(randomId());
  const [creating, setCreating] = useState(false);
  const [created, setCreated] = useState<ScenarioInstance | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function generate() {
    if (!requirement.trim() || generating) return;
    setGenerating(true);
    setError(null);
    setDraft(null);
    setCreated(null);
    try {
      const res = await fetch("/api/scenario-generator/draft", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ requirement }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? "Generation failed");
      setDraft((await res.json()) as GeneratedScenarioConfig);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setGenerating(false);
    }
  }

  async function create() {
    if (!draft || creating) return;
    setCreating(true);
    setError(null);
    try {
      const res = await fetch("/api/scenario-instances", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ cohort_id: cohortId, student_id: studentId, config: draft }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? "Creation failed");
      const instance = (await res.json()) as ScenarioInstance;
      setCreated(instance);
      setStudentId(randomId());
      onCreated();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setCreating(false);
    }
  }

  return (
    <section className="card">
      <div className="card-header">
        <Sparkles size={17} />
        <h2>Generate a scenario</h2>
      </div>
      <p className="empty-state" style={{ marginBottom: "0.75rem" }}>
        Paste a raw client requirement — the generator drafts a persona, a synthetic-dataset shape, and a graded
        technical task (an executable SQL query, not a prose rubric) from it.
      </p>

      <div className="chat-input" style={{ alignItems: "flex-start" }}>
        <textarea
          value={requirement}
          onChange={(e) => setRequirement(e.target.value)}
          placeholder="e.g. Client's nightly CRM sync keeps duplicating orders and support is drowning in tickets about it…"
          rows={3}
          style={{ flex: 1 }}
        />
        <button onClick={generate} disabled={generating || !requirement.trim()}>
          {generating ? "Drafting…" : "Generate"}
        </button>
      </div>

      {error && (
        <p className="error-text">
          <AlertCircle size={14} /> {error}
        </p>
      )}

      {draft && (
        <div style={{ marginTop: "1rem" }}>
          <p className="dataset-link">
            Domain: {draft.data_gen.domain} · Messiness: {draft.data_gen.messiness}
            {draft.legacy_system && <> · Legacy system: {draft.legacy_system.scenario_id}</>}
          </p>

          <p className="empty-state" style={{ marginTop: "0.5rem" }}>
            <strong style={{ color: "var(--ink-900)" }}>Persona:</strong> {draft.persona.system_prompt}
          </p>
          <p className="empty-state">
            <strong style={{ color: "var(--ink-900)" }}>Agenda:</strong> {draft.persona.agenda}
          </p>

          <p className="empty-state" style={{ marginTop: "0.5rem" }}>
            <strong style={{ color: "var(--ink-900)" }}>Technical task:</strong> {draft.technical_task.instructions}
          </p>
          <pre className="submission-content" style={{ fontFamily: "var(--font-mono)" }}>
            {draft.technical_task.task_type === "python_script"
              ? draft.technical_task.reference_solution
              : draft.technical_task.reference_query}
          </pre>

          <div className="chat-input" style={{ marginTop: "0.85rem" }}>
            <input
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              placeholder="Student ID"
              style={{ flex: 1 }}
            />
            <button onClick={create} disabled={creating}>
              {creating ? "Creating…" : "Create & add to cohort"}
            </button>
          </div>

          {created && (
            <div className="submission-result passed" style={{ marginTop: "0.75rem" }}>
              <div className="submission-result-head">
                <CheckCircle2 size={16} /> Scenario instance created ({created.id.slice(0, 8)}).
              </div>
              <p className="submission-status">
                One more step: this scenario needs a synthetic dataset before its technical task can be graded —
                run:
              </p>
              <pre className="submission-content">
                {`docker compose run --rm data-gen python -m generator ${created.id}`}
              </pre>
              <p className="submission-status">Then schedule the cohort above to make it active.</p>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
