import { AlertCircle } from "lucide-react";
import AppShell from "../../../components/AppShell";
import { listCohortInstances, UpstreamError } from "../../../lib/backend";
import InstructorConsole from "../../../components/InstructorConsole";

export default async function InstructorCohortPage({ params }: { params: { cohortId: string } }) {
  let instances;
  try {
    instances = await listCohortInstances(params.cohortId);
  } catch (err) {
    const status = err instanceof UpstreamError ? err.status : 502;
    return (
      <AppShell role="Instructor">
        <main className="page">
          <p className="error-text">
            <AlertCircle size={14} /> Couldn&apos;t load cohort {params.cohortId} (status {status}):{" "}
            {(err as Error).message}
          </p>
        </main>
      </AppShell>
    );
  }

  return <InstructorConsole cohortId={params.cohortId} initialInstances={instances} />;
}
