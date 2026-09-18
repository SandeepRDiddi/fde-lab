"use client";

import { useEffect, useState } from "react";
import type { ScenarioInstance } from "../lib/types";

function formatRemaining(ms: number): string {
  if (ms <= 0) return "0:00:00";
  const totalSeconds = Math.floor(ms / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return `${hours}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

const STATUS_LABEL: Record<ScenarioInstance["status"], string> = {
  not_started: "Not started",
  active: "Active",
  closed: "Closed",
};

export default function ScenarioStatusHeader({ instance }: { instance: ScenarioInstance }) {
  // Starts null (not Date.now()) so the server-rendered and pre-hydration
  // client markup match exactly -- the countdown only appears once the
  // client has actually mounted and a real "now" is available.
  const [now, setNow] = useState<number | null>(null);

  useEffect(() => {
    setNow(Date.now());
    if (instance.status !== "active" || !instance.end_at) return;
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [instance.status, instance.end_at]);

  return (
    <header className="status-header">
      <div className={`status-badge status-${instance.status}`}>{STATUS_LABEL[instance.status]}</div>

      {instance.status === "active" && instance.end_at && now !== null && (
        <div className="status-remaining">
          Time remaining: <strong>{formatRemaining(new Date(instance.end_at).getTime() - now)}</strong>
        </div>
      )}

      {instance.status === "not_started" && instance.start_at && (
        <div className="status-remaining">Opens at {new Date(instance.start_at).toLocaleString()}</div>
      )}

      {instance.status === "closed" && instance.end_at && (
        <div className="status-remaining">Closed at {new Date(instance.end_at).toLocaleString()}</div>
      )}
    </header>
  );
}
