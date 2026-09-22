import { NextResponse } from "next/server";
import { getEngagement, UpstreamError } from "../../../../lib/backend";

export async function GET(_req: Request, { params }: { params: { engagementId: string } }) {
  try {
    const engagement = await getEngagement(params.engagementId);
    return NextResponse.json(engagement);
  } catch (err) {
    const status = err instanceof UpstreamError ? err.status : 502;
    return NextResponse.json({ detail: (err as Error).message }, { status });
  }
}
