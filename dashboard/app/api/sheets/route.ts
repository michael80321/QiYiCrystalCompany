import { NextRequest, NextResponse } from "next/server";
import { getRecords, appendRow, updateCell } from "@/lib/sheets";

export async function GET(req: NextRequest) {
  const tab = req.nextUrl.searchParams.get("tab");
  if (!tab) return NextResponse.json({ error: "tab required" }, { status: 400 });
  try {
    const data = await getRecords(tab);
    return NextResponse.json(data);
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const { action, tab, row, col, value, rowData } = body;
  try {
    if (action === "append") {
      await appendRow(tab, rowData);
    } else if (action === "update") {
      await updateCell(tab, row, col, value);
    }
    return NextResponse.json({ ok: true });
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
