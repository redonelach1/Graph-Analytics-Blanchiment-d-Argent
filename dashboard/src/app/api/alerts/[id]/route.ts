import { NextResponse } from "next/server";
import { getAlertById } from "@/lib/data-service";

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const alert = await getAlertById(params.id);
    if (!alert) {
      return NextResponse.json(
        { status: "error", message: `Alert with ID ${params.id} not found` },
        { status: 404 }
      );
    }

    return NextResponse.json({
      status: "success",
      alert,
    });
  } catch (error) {
    return NextResponse.json(
      { status: "error", message: "Failed to fetch alert dossier", details: String(error) },
      { status: 500 }
    );
  }
}

