import { listCohortInstances, UpstreamError } from "../../../lib/backend";
import InstructorConsole from "../../../components/InstructorConsole";

export default async function InstructorCohortPage({ params }: { params: { cohortId: string } }) {
  let instances;
  try {
    instances = await listCohortInstances(params.cohortId);
  } catch (err) {
    const status = err instanceof UpstreamError ? err.status : 502;
    return (
      <main className="workspace">
        <p className="error-text">
          Couldn&apos;t load cohort {params.cohortId} (status {status}): {(err as Error).message}
        </p>
      </main>
    );
  }

  return <InstructorConsole cohortId={params.cohortId} initialInstances={instances} />;
}
