import { NextResponse } from "next/server";
import { submitToBackend, UpstreamError } from "../../../../../lib/backend";

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
    // The backend evaluates compliance itself (app/compliance.py) and
    // rejects a failing submission with a 422 rather than persisting it --
    // submitToBackend normalizes both outcomes into the same shape.
    const result = await submitToBackend(params.instanceId, content);
    return NextResponse.json(result);
  } catch (err) {
    const status = err instanceof UpstreamError ? err.status : 502;
    return NextResponse.json({ detail: (err as Error).message }, { status });
  }
}
