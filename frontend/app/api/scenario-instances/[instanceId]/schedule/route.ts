import { NextResponse } from "next/server";
import { scheduleScenarioInstance, UpstreamError } from "../../../../../lib/backend";
import type { ScenarioSchedule } from "../../../../../lib/types";

export async function POST(req: Request, { params }: { params: { instanceId: string } }) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ detail: "Request body must be valid JSON" }, { status: 400 });
  }
  const { start_at: startAt, end_at: endAt, pivot_at: pivotAt, pivot_config: pivotConfig } = body as Partial<
    ScenarioSchedule
  >;
  if (!startAt || !endAt) {
    return NextResponse.json({ detail: "start_at and end_at are required" }, { status: 400 });
  }

  try {
    const instance = await scheduleScenarioInstance(params.instanceId, {
      start_at: startAt,
      end_at: endAt,
      pivot_at: pivotAt ?? null,
      pivot_config: pivotConfig ?? null,
    });
    return NextResponse.json(instance);
  } catch (err) {
    const status = err instanceof UpstreamError ? err.status : 502;
    return NextResponse.json({ detail: (err as Error).message }, { status });
  }
}
