import { NextResponse } from "next/server";
import { createGlobalRetailEngagement, UpstreamError } from "../../../../lib/backend";

export async function POST(req: Request) {
  try {
    const { cohort_id, student_id } = await req.json();
    const engagement = await createGlobalRetailEngagement(cohort_id, student_id);
    return NextResponse.json(engagement, { status: 201 });
  } catch (err) {
    const status = err instanceof UpstreamError ? err.status : 502;
    return NextResponse.json({ detail: (err as Error).message }, { status });
  }
}
