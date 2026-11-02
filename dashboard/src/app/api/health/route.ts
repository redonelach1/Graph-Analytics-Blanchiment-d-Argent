import { NextResponse } from "next/server";
import { getPipelineHealth } from "@/lib/data-service";

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

