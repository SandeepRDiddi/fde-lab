"use client";

import { useState } from "react";
import { AlertCircle, Server } from "lucide-react";
import type { LegacySystemConfig } from "../lib/types";

export default function LegacySystemPanel({
  instanceId,
  legacySystem,
}: {
  instanceId: string;
  legacySystem?: LegacySystemConfig;
}) {
  const [authValue, setAuthValue] = useState("");
  const [querying, setQuerying] = useState(false);
  const [statusCode, setStatusCode] = useState<number | null>(null);
  const [body, setBody] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function query() {
    setQuerying(true);
    setError(null);
    try {
      const url = new URL(`/api/scenario-instances/${instanceId}/legacy-system`, window.location.origin);
      if (authValue.trim()) url.searchParams.set("auth", authValue.trim());
      const res = await fetch(url.toString());
      setStatusCode(res.status);
      const text = await res.text();
      try {
        setBody(JSON.stringify(JSON.parse(text), null, 2));
      } catch {
        setBody(text);
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setQuerying(false);
    }
  }

  return (
    <section className="card">
      <div className="card-header">
        <Server size={17} />
        <h2>Legacy system</h2>
      </div>

      {!legacySystem ? (
        <p className="empty-state">
          <Server size={14} /> No legacy system configured for this scenario.
        </p>
      ) : (
        <>
          {legacySystem.description && <p className="empty-state">{legacySystem.description}</p>}
          <p className="dataset-link" style={{ marginBottom: "0.75rem" }}>
            GET /{legacySystem.scenario_id}
            {legacySystem.path}
          </p>

          {legacySystem.auth_header_name && (
            <div className="chat-input" style={{ marginBottom: "0.75rem" }}>
              <input
                type="text"
                value={authValue}
                onChange={(e) => setAuthValue(e.target.value)}
                placeholder={`${legacySystem.auth_header_name} value (if you have it)`}
                style={{ flex: 1 }}
              />
            </div>
          )}

          <button className="btn-secondary" onClick={query} disabled={querying}>
            {querying ? "Querying…" : "Query system"}
          </button>

          {error && (
            <p className="error-text">
              <AlertCircle size={14} /> {error}
            </p>
          )}

          {statusCode !== null && (
            <div style={{ marginTop: "0.85rem" }}>
              <span
                className={`approval-badge ${statusCode < 300 ? "approval-approved" : "approval-rejected"}`}
                style={{ marginBottom: "0.5rem", display: "inline-flex" }}
              >
                HTTP {statusCode}
              </span>
              <pre className="submission-content">{body}</pre>
            </div>
          )}
        </>
      )}
    </section>
  );
}
