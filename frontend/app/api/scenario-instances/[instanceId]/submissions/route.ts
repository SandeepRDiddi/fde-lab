import { NextResponse } from "next/server";
import { listSubmissions, UpstreamError } from "../../../../../lib/backend";

export async function GET(_req: Request, { params }: { params: { instanceId: string } }) {
  try {
    const submissions = await listSubmissions(params.instanceId);
    return NextResponse.json(submissions);
  } catch (err) {
    const status = err instanceof UpstreamError ? err.status : 502;
    return NextResponse.json({ detail: (err as Error).message }, { status });
  }
}
