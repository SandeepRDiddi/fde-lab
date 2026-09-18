export default function DatasetLink({ location }: { location: string | null }) {
  return (
    <section className="panel">
      <h2>Dataset</h2>
      {location ? (
        <a href={location} target="_blank" rel="noreferrer" className="dataset-link">
          {location}
        </a>
      ) : (
        <p className="empty-state">Dataset hasn&apos;t been generated for this instance yet.</p>
      )}
    </section>
  );
}
