import { NextResponse } from "next/server";
import { getAlerts } from "@/lib/data-service";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const risk = searchParams.get("risk");

    let alerts = await getAlerts();
    if (risk && risk !== "ALL") {
      alerts = alerts.filter((a) => a.risk_level.toUpperCase() === risk.toUpperCase());
    }

    return NextResponse.json({
      status: "success",
      count: alerts.length,
      alerts,
    });
  } catch (error) {
    return NextResponse.json(
      { status: "error", message: "Failed to fetch fraud alerts", details: String(error) },
      { status: 500 }
    );
  }
}

