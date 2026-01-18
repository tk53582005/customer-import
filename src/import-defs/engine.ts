// src/import-defs/engine.ts
import type { ImportDefinition, FieldMapping } from "./types";
import { applyNormalizers } from "./normalizers";
import { validateValue } from "./validators";

export type RowInput = Record<string, unknown>; // previewの1行（Excel列名 -> 値）
export type RowProcessed = {
  raw: RowInput;
  mapped: Record<string, string>;      // fieldKey -> raw string
  normalized: Record<string, string>;  // fieldKey -> normalized string (+ computed)
  errors: Array<{
    fieldKey: string;
    fieldLabel: string;
    code: string;
    message: string;
  }>;
};

export function mapRowToFields(
  row: RowInput,
  mapping: FieldMapping,
  def: ImportDefinition
): Record<string, string> {
  const mapped: Record<string, string> = {};
  for (const f of def.fields) {
    const sourceCol = mapping[f.key];
    const rawVal = sourceCol ? row[sourceCol] : "";
    mapped[f.key] = rawVal == null ? "" : String(rawVal);
  }
  return mapped;
}

export function normalizeMapped(
  mapped: Record<string, string>,
  def: ImportDefinition
): Record<string, string> {
  const normalized: Record<string, string> = {};

  for (const f of def.fields) {
    const params = f.normalizer_params ?? {};
    normalized[f.key] = applyNormalizers(mapped[f.key], f.normalizers ?? [], params);
  }

  // computed_fields（email_norm / phone_norm など）
  for (const cf of def.computed_fields ?? []) {
    const src = normalized[cf.from] ?? mapped[cf.from] ?? "";
    normalized[cf.key] = applyNormalizers(src, cf.normalizers ?? [], {});
  }

  return normalized;
}

export function validateRow(
  row: RowInput,
  mapping: FieldMapping,
  def: ImportDefinition
): RowProcessed {
  const mapped = mapRowToFields(row, mapping, def);
  const normalized = normalizeMapped(mapped, def);

  const errors: RowProcessed["errors"] = [];
  for (const f of def.fields) {
    // enum_map で default に倒してる場合でも、validatorsで最終チェック
    const errs = validateValue(f, normalized[f.key] ?? "");
    errors.push(...errs);
  }

  return { raw: row, mapped, normalized, errors };
}