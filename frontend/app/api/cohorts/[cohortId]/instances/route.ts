import { NextResponse } from "next/server";
import { listCohortInstances, UpstreamError } from "../../../../../lib/backend";

export async function GET(_req: Request, { params }: { params: { cohortId: string } }) {
  try {
    const instances = await listCohortInstances(params.cohortId);
    return NextResponse.json(instances);
  } catch (err) {
    const status = err instanceof UpstreamError ? err.status : 502;
    return NextResponse.json({ detail: (err as Error).message }, { status });
  }
}
