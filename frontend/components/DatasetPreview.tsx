"use client";

import { useEffect, useState } from "react";
import { AlertCircle, Database } from "lucide-react";
import type { DatasetPreview as DatasetPreviewData } from "../lib/types";

export default function DatasetPreview({ instanceId, hasDataset }: { instanceId: string; hasDataset: boolean }) {
  const [preview, setPreview] = useState<DatasetPreviewData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!hasDataset) return;
    setLoading(true);
    setError(null);
    fetch(`/api/scenario-instances/${instanceId}/dataset-preview?limit=20`)
      .then(async (res) => {
        if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? "Failed to load dataset");
        return res.json() as Promise<DatasetPreviewData>;
      })
      .then(setPreview)
      .catch((err) => setError((err as Error).message))
      .finally(() => setLoading(false));
  }, [instanceId, hasDataset]);

  return (
    <section className="card">
      <div className="card-header">
        <Database size={17} />
        <h2>Dataset</h2>
      </div>

      {!hasDataset && (
        <p className="empty-state">
          <Database size={14} /> Dataset hasn&apos;t been generated for this instance yet.
        </p>
      )}

      {hasDataset && loading && <p className="empty-state">Loading preview…</p>}

      {error && (
        <p className="error-text">
          <AlertCircle size={14} /> {error}
        </p>
      )}

      {preview && (
        <>
          <p className="dataset-link" style={{ marginBottom: "0.6rem" }}>
            {preview.total_rows} row{preview.total_rows === 1 ? "" : "s"} total — showing first{" "}
            {preview.rows.length}
          </p>
          <div className="table-scroll">
            <table className="roster-table">
              <thead>
                <tr>
                  {preview.columns.map((col) => (
                    <th key={col}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.rows.map((row, i) => (
                  <tr key={i}>
                    {preview.columns.map((col) => (
                      <td key={col} style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>
                        {row[col] === null || row[col] === undefined ? (
                          <span className="empty-state" style={{ display: "inline" }}>
                            null
                          </span>
                        ) : (
                          String(row[col])
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}
