// src/import-csv/parseCsv.ts
import Papa from "papaparse";

export type CsvParseResult = {
  columns: string[];
  rows: Record<string, unknown>[];
};

export async function parseCsvFile(file: File): Promise<CsvParseResult> {
  const text = await file.text();

  const parsed = Papa.parse<Record<string, unknown>>(text, {
    header: true,
    skipEmptyLines: true,
    transformHeader: (h) => String(h ?? "").trim(),
  });

  if (parsed.errors?.length) {
    // 先頭だけ投げる（UIで表示しやすい）
    const e = parsed.errors[0];
    throw new Error(`CSV parse error: ${e.message} (row=${e.row})`);
  }

  const rows = (parsed.data ?? []).filter((r) => r && Object.keys(r).length > 0);

  // columnsは、header:true の場合 parsed.meta.fields に入る
  const columns = (parsed.meta.fields ?? []).map((c) => String(c).trim()).filter(Boolean);

  return { columns, rows };
}