import { NextResponse } from "next/server";
import { generateScenarioDraft, UpstreamError } from "../../../../lib/backend";

export async function POST(req: Request) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ detail: "Request body must be valid JSON" }, { status: 400 });
  }
  const { requirement } = body as { requirement?: string };
  if (!requirement || !requirement.trim()) {
    return NextResponse.json({ detail: "requirement is required" }, { status: 400 });
  }

  try {
    const config = await generateScenarioDraft(requirement);
    return NextResponse.json(config);
  } catch (err) {
    const status = err instanceof UpstreamError ? err.status : 502;
    return NextResponse.json({ detail: (err as Error).message }, { status });
  }
}
