"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function InstructorLandingPage() {
  const router = useRouter();
  const [cohortId, setCohortId] = useState("");

  function goToCohort() {
    const trimmed = cohortId.trim();
    if (!trimmed) return;
    router.push(`/instructor/${trimmed}`);
  }

  return (
    <main className="workspace">
      <h1>Instructor console</h1>
      <section className="panel">
        <h2>Open a cohort</h2>
        <div className="chat-input">
          <input
            value={cohortId}
            onChange={(e) => setCohortId(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && goToCohort()}
            placeholder="Cohort ID"
          />
          <button onClick={goToCohort} disabled={!cohortId.trim()}>
            Open
          </button>
        </div>
      </section>
    </main>
  );
}
