import { Inbox, Mail } from "lucide-react";
import type { ArtifactInject } from "../lib/types";

export default function ArtifactFeed({ artifacts }: { artifacts: ArtifactInject[] }) {
  return (
    <section className="card">
      <div className="card-header">
        <Mail size={17} />
        <h2>Artifacts &amp; tickets</h2>
      </div>
      {artifacts.length === 0 ? (
        <p className="empty-state">
          <Inbox size={14} /> Nothing has come in yet.
        </p>
      ) : (
        <ul className="artifact-feed">
          {artifacts.map((artifact) => (
            <li key={artifact.id} className="artifact-card">
              <div className="artifact-meta">
                <span className="artifact-type">{artifact.type}</span>
                {artifact.from && <span className="artifact-from">from {artifact.from}</span>}
              </div>
              <h3>{artifact.title}</h3>
              <p>{artifact.body}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
