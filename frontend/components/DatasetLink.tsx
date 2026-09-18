import { Database, ExternalLink } from "lucide-react";

export default function DatasetLink({ location }: { location: string | null }) {
  return (
    <section className="card">
      <div className="card-header">
        <Database size={17} />
        <h2>Dataset</h2>
      </div>
      {location ? (
        <a href={location} target="_blank" rel="noreferrer" className="dataset-link">
          <ExternalLink size={13} /> {location}
        </a>
      ) : (
        <p className="empty-state">
          <Database size={14} /> Dataset hasn&apos;t been generated for this instance yet.
        </p>
      )}
    </section>
  );
}
