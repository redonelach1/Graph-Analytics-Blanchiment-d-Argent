import { NextResponse } from "next/server";
import { getPipelineHealth } from "@/lib/data-service";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET() {
  try {
    const health = await getPipelineHealth();
    return NextResponse.json({
      status: "success",
      health,
    });
  } catch (error) {
    return NextResponse.json(
      { status: "error", message: "Failed to fetch pipeline health", details: String(error) },
      { status: 500 }
    );
  }
}

