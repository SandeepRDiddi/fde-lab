import { NextResponse } from "next/server";
import { getDatasetPreview, UpstreamError } from "../../../../../lib/backend";

export async function GET(req: Request, { params }: { params: { instanceId: string } }) {
  const limitParam = new URL(req.url).searchParams.get("limit");
  const limit = limitParam ? Number(limitParam) : undefined;

  try {
    const preview = await getDatasetPreview(params.instanceId, limit);
    return NextResponse.json(preview);
  } catch (err) {
    const status = err instanceof UpstreamError ? err.status : 502;
    return NextResponse.json({ detail: (err as Error).message }, { status });
  }
}
