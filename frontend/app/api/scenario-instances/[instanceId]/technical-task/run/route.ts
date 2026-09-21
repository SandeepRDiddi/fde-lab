import { NextResponse } from "next/server";
import { runTechnicalTaskQuery, UpstreamError } from "../../../../../../lib/backend";

export async function POST(req: Request, { params }: { params: { instanceId: string } }) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ detail: "Request body must be valid JSON" }, { status: 400 });
  }
  const { content } = body as { content?: string };
  if (!content || !content.trim()) {
    return NextResponse.json({ detail: "content is required" }, { status: 400 });
  }

  try {
    const result = await runTechnicalTaskQuery(params.instanceId, content);
    return NextResponse.json(result);
  } catch (err) {
    const status = err instanceof UpstreamError ? err.status : 502;
    return NextResponse.json({ detail: (err as Error).message }, { status });
  }
}
