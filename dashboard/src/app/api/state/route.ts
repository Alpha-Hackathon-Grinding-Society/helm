import { NextResponse } from "next/server";
import { loadDeployment } from "@/lib/deployment";
import { readChainStateWithTimeout } from "@/lib/chain";

export const dynamic = "force-dynamic";
export const revalidate = 0;

/**
 * The live state of both chains, as JSON.
 *
 * The dashboard pages read the chains server-side, but a judge who wants the raw numbers
 * — or a script that wants to poll Helm — can get them from here.
 */
export async function GET() {
  const deployment = await loadDeployment();
  const snapshot = await readChainStateWithTimeout(deployment);
  return NextResponse.json(snapshot, {
    headers: { "cache-control": "no-store" },
  });
}
