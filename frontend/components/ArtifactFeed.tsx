import type { ArtifactInject } from "../lib/types";

export default function ArtifactFeed({ artifacts }: { artifacts: ArtifactInject[] }) {
  if (artifacts.length === 0) {
    return (
      <section className="panel">
        <h2>Artifacts &amp; tickets</h2>
        <p className="empty-state">Nothing has come in yet.</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <h2>Artifacts &amp; tickets</h2>
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
    </section>
  );
}
