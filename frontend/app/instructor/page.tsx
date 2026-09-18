"use client";

import { ArrowRight, LayoutDashboard } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import AppShell from "../../components/AppShell";

export default function InstructorLandingPage() {
  const router = useRouter();
  const [cohortId, setCohortId] = useState("");

  function goToCohort() {
    const trimmed = cohortId.trim();
    if (!trimmed) return;
    router.push(`/instructor/${trimmed}`);
  }

  return (
    <AppShell role="Instructor">
      <main className="page">
        <div className="page-header">
          <span className="page-eyebrow">Cohort management</span>
          <h1>Instructor console</h1>
          <p className="page-subtitle">Open a cohort to schedule its scenario and review student submissions.</p>
        </div>
        <section className="card" style={{ maxWidth: 460 }}>
          <div className="card-header">
            <LayoutDashboard size={17} />
            <h2>Open a cohort</h2>
          </div>
          <div className="chat-input">
            <input
              value={cohortId}
              onChange={(e) => setCohortId(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && goToCohort()}
              placeholder="Cohort ID"
              style={{ width: "100%" }}
            />
            <button onClick={goToCohort} disabled={!cohortId.trim()}>
              Open <ArrowRight size={14} />
            </button>
          </div>
        </section>
      </main>
    </AppShell>
  );
}
