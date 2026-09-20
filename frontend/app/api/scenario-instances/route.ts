import { NextResponse } from "next/server";
import { createScenarioInstance, UpstreamError } from "../../../lib/backend";

export async function POST(req: Request) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ detail: "Request body must be valid JSON" }, { status: 400 });
  }
  const { cohort_id: cohortId, student_id: studentId, config } = body as {
    cohort_id?: string;
    student_id?: string;
    config?: Record<string, unknown>;
  };
  if (!cohortId || !studentId) {
    return NextResponse.json({ detail: "cohort_id and student_id are required" }, { status: 400 });
  }

  try {
    const instance = await createScenarioInstance(cohortId, studentId, config ?? {});
    return NextResponse.json(instance, { status: 201 });
  } catch (err) {
    const status = err instanceof UpstreamError ? err.status : 502;
    return NextResponse.json({ detail: (err as Error).message }, { status });
  }
}
