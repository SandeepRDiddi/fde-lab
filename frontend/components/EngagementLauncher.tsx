"use client";

import { useState } from "react";
import { AlertCircle, Rocket } from "lucide-react";

// FDE-041: launches the GlobalRetail worked-example engagement (FDE-018's
// POST /engagements/global-retail) for one student, and hands back the
// link to /engagement/<id> -- the instructor's one-click way to get a
// student into the 22-stage engagement rather than assembling a scenario
// config by hand.
export default function EngagementLauncher({ cohortId }: { cohortId: string }) {
  const [studentId, setStudentId] = useState("");
  const [launching, setLaunching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [link, setLink] = useState<string | null>(null);

  async function launch() {
    if (!studentId.trim() || launching) return;
    setLaunching(true);
    setError(null);
    setLink(null);
    try {
      const res = await fetch("/api/engagements/global-retail", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ cohort_id: cohortId, student_id: studentId.trim() }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? "Launch failed");
      const engagement = (await res.json()) as { id: string };
      setLink(`/engagement/${engagement.id}`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLaunching(false);
    }
  }

  return (
    <section className="card">
      <div className="card-header">
        <Rocket size={17} />
        <h2>Launch GlobalRetail engagement</h2>
      </div>
      <p className="empty-state" style={{ marginBottom: "0.75rem" }}>
        Starts the 22-stage FDE Engagement Framework (GlobalRetail worked example) for one student.
      </p>
      <div className="schedule-form">
        <label>
          Student ID
          <input
            type="text"
            value={studentId}
            onChange={(e) => setStudentId(e.target.value)}
            placeholder="student UUID"
          />
        </label>
        <button onClick={launch} disabled={launching || !studentId.trim()}>
          {launching ? "Launching…" : "Launch"}
        </button>
      </div>
      {error && (
        <p className="error-text">
          <AlertCircle size={14} /> {error}
        </p>
      )}
      {link && (
        <p className="empty-state">
          Ready: <a href={link}>{link}</a>
        </p>
      )}
    </section>
  );
}
