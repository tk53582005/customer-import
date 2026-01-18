// src/import-xlsx/parseXlsx.ts
import * as XLSX from "xlsx";

export type XlsxParseResult = {
  columns: string[];
  rows: Record<string, unknown>[];
};

function normalizeHeader(h: unknown): string {
  return String(h ?? "").trim();
}

function isEmptyRow(obj: Record<string, unknown>): boolean {
  return Object.values(obj).every((v) => String(v ?? "").trim() === "");
}

/**
 * Excel(.xlsx) -> { columns, rows }
 * - 1枚目のシートを読む
 * - 1行目をヘッダー扱い
 * - 空行は除外
 */
export async function parseXlsxFile(file: File): Promise<XlsxParseResult> {
  const buffer = await file.arrayBuffer();
  const wb = XLSX.read(buffer, { type: "array" });

  const sheetName = wb.SheetNames?.[0];
  if (!sheetName) throw new Error("シートが見つかりませんでした");

  const ws = wb.Sheets[sheetName];
  if (!ws) throw new Error("ワークシートの読み込みに失敗しました");

  // sheet_to_json を header:1 で 2D配列として取得
  const data = XLSX.utils.sheet_to_json(ws, {
    header: 1,
    raw: false,       // 可能な範囲で文字列化（Lv1向け）
    blankrows: false, // 空行は落とす
    defval: "",       // undefinedを空文字へ
  }) as unknown[][];

  if (!data || data.length === 0) throw new Error("Excelにデータがありません");

  // 1行目 = header
  const headerRow = (data[0] ?? []).map(normalizeHeader).filter(Boolean);
  if (headerRow.length === 0) throw new Error("ヘッダー行（1行目）が空です");

  // 2行目以降 = rows
  const rows: Record<string, unknown>[] = [];
  for (let i = 1; i < data.length; i++) {
    const rowArr = data[i] ?? [];
    const obj: Record<string, unknown> = {};

    for (let c = 0; c < headerRow.length; c++) {
      const key = headerRow[c];
      obj[key] = rowArr[c] ?? "";
    }

    if (!isEmptyRow(obj)) rows.push(obj);
  }

  return {
    columns: headerRow,
    rows,
  };
}