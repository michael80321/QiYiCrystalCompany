import { google } from "googleapis";

const SHEETS_ID = process.env.SHEETS_ID!;

function getAuth() {
  const credJson = process.env.GOOGLE_SERVICE_ACCOUNT_JSON!;
  const creds = JSON.parse(credJson);
  return new google.auth.GoogleAuth({
    credentials: creds,
    scopes: ["https://www.googleapis.com/auth/spreadsheets"],
  });
}

export async function getSheetData(tabName: string): Promise<string[][]> {
  const auth = getAuth();
  const sheets = google.sheets({ version: "v4", auth });
  const res = await sheets.spreadsheets.values.get({
    spreadsheetId: SHEETS_ID,
    range: tabName,
  });
  return (res.data.values as string[][]) ?? [];
}

export async function appendRow(tabName: string, row: string[]) {
  const auth = getAuth();
  const sheets = google.sheets({ version: "v4", auth });
  await sheets.spreadsheets.values.append({
    spreadsheetId: SHEETS_ID,
    range: `${tabName}!A1`,
    valueInputOption: "USER_ENTERED",
    requestBody: { values: [row] },
  });
}

export async function updateCell(tabName: string, row: number, col: number, value: string) {
  const auth = getAuth();
  const sheets = google.sheets({ version: "v4", auth });
  const colLetter = String.fromCharCode(64 + col);
  await sheets.spreadsheets.values.update({
    spreadsheetId: SHEETS_ID,
    range: `${tabName}!${colLetter}${row}`,
    valueInputOption: "USER_ENTERED",
    requestBody: { values: [[value]] },
  });
}

function rowsToObjects(rows: string[][]): Record<string, string>[] {
  if (rows.length < 2) return [];
  const headers = rows[0];
  return rows.slice(1).map((row) =>
    Object.fromEntries(headers.map((h, i) => [h, row[i] ?? ""]))
  );
}

export async function getRecords(tabName: string): Promise<Record<string, string>[]> {
  const rows = await getSheetData(tabName);
  return rowsToObjects(rows);
}
