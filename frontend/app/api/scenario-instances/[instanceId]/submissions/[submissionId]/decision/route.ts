import { NextResponse } from "next/server";
import { decideSubmission, UpstreamError } from "../../../../../../../lib/backend";
import type { ApprovalStatus } from "../../../../../../../lib/types";

export async function PATCH(
  req: Request,
  { params }: { params: { instanceId: string; submissionId: string } }
) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ detail: "Request body must be valid JSON" }, { status: 400 });
  }
  const { decision } = body as { decision?: ApprovalStatus };
  if (decision !== "approved" && decision !== "rejected") {
    return NextResponse.json({ detail: "decision must be 'approved' or 'rejected'" }, { status: 400 });
  }

  try {
    const submission = await decideSubmission(params.instanceId, params.submissionId, decision);
    return NextResponse.json(submission);
  } catch (err) {
    const status = err instanceof UpstreamError ? err.status : 502;
    return NextResponse.json({ detail: (err as Error).message }, { status });
  }
}
