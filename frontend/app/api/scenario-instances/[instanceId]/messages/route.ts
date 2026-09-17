import { NextResponse } from "next/server";
import { getConversation, sendMessage, UpstreamError } from "../../../../../lib/backend";

export async function GET(req: Request, { params }: { params: { instanceId: string } }) {
  const studentId = new URL(req.url).searchParams.get("student_id");
  if (!studentId) {
    return NextResponse.json({ detail: "student_id is required" }, { status: 400 });
  }
  try {
    const conversation = await getConversation(params.instanceId, studentId);
    return NextResponse.json(conversation);
  } catch (err) {
    const status = err instanceof UpstreamError ? err.status : 502;
    return NextResponse.json({ detail: (err as Error).message }, { status });
  }
}

export async function POST(req: Request, { params }: { params: { instanceId: string } }) {
  const body = await req.json();
  const { student_id: studentId, message } = body as { student_id?: string; message?: string };
  if (!studentId || !message) {
    return NextResponse.json({ detail: "student_id and message are required" }, { status: 400 });
  }
  try {
    const reply = await sendMessage(params.instanceId, studentId, message);
    return NextResponse.json(reply, { status: 201 });
  } catch (err) {
    const status = err instanceof UpstreamError ? err.status : 502;
    return NextResponse.json({ detail: (err as Error).message }, { status });
  }
}
