import { NextResponse } from "next/server";
import { getScenarioInstance, UpstreamError } from "../../../../lib/backend";

export async function GET(_req: Request, { params }: { params: { instanceId: string } }) {
  try {
    const instance = await getScenarioInstance(params.instanceId);
    return NextResponse.json(instance);
  } catch (err) {
    const status = err instanceof UpstreamError ? err.status : 502;
    return NextResponse.json({ detail: (err as Error).message }, { status });
  }
}
