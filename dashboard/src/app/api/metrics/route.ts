import { NextResponse } from "next/server";
import { getAccountMetrics } from "@/lib/data-service";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET() {
  try {
    const metrics = await getAccountMetrics();
    return NextResponse.json({
      status: "success",
      count: metrics.length,
      metrics,
    });
  } catch (error) {
    return NextResponse.json(
      { status: "error", message: "Failed to fetch account metrics", details: String(error) },
      { status: 500 }
    );
  }
}

