import { NextResponse } from "next/server";
import { getScenarioInstance, submitToBackend, UpstreamError } from "../../../../../lib/backend";
import { evaluateSubmission } from "../../../../../lib/compliance";

export async function POST(req: Request, { params }: { params: { instanceId: string } }) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ detail: "Request body must be valid JSON" }, { status: 400 });
  }
  const { student_id: studentId, content } = body as { student_id?: string; content?: string };
  if (!studentId || !content) {
    return NextResponse.json({ detail: "student_id and content are required" }, { status: 400 });
  }

  try {
    const fromBackend = await submitToBackend(params.instanceId, studentId, content);
    if (fromBackend) return NextResponse.json(fromBackend);

    // No backend submissions endpoint yet — fall back to the local
    // compliance stand-in (see lib/compliance.ts).
    const instance = await getScenarioInstance(params.instanceId);
    const rules = instance.config.compliance_checklist ?? [];
    const result = evaluateSubmission(content, rules);
    return NextResponse.json(result);
  } catch (err) {
    const status = err instanceof UpstreamError ? err.status : 502;
    return NextResponse.json({ detail: (err as Error).message }, { status });
  }
}
