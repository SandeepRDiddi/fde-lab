import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function GET(req: Request, { params }: { params: { instanceId: string } }) {
  const auth = new URL(req.url).searchParams.get("auth");

  let upstream: Response;
  try {
    upstream = await fetch(`${BACKEND_URL}/scenario-instances/${params.instanceId}/legacy-system`, {
      headers: auth ? { "X-Legacy-Auth": auth } : {},
      cache: "no-store",
    });
  } catch (err) {
    return NextResponse.json({ detail: `Legacy system unreachable: ${(err as Error).message}` }, { status: 502 });
  }

  // Relay the backend's response (and therefore the mock's) exactly as-is --
  // status code included. A 401 with its deliberately unhelpful body is
  // useful information for the student, not an error this route should hide.
  const body = await upstream.text();
  return new NextResponse(body, {
    status: upstream.status,
    headers: { "content-type": upstream.headers.get("content-type") ?? "application/json" },
  });
}
