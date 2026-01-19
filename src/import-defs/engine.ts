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

// 候補検出のための類似度計算
export type DuplicateCandidate = {
  candidateIndex: number;  // previewRows内のインデックス
  matchType: 'name_address' | 'name_only' | 'address_only';
  score: number;  // 0-100
  reason: string;
};

export type RowWithCandidates = RowProcessed & {
  candidates: DuplicateCandidate[];
};

// シンプルな文字列類似度（Levenshtein距離の簡易版）
function similarity(a: string, b: string): number {
  if (a === b) return 100;
  if (!a || !b) return 0;
  
  const longer = a.length > b.length ? a : b;
  const shorter = a.length > b.length ? b : a;
  
  if (longer.length === 0) return 100;
  
  const editDistance = levenshteinDistance(longer, shorter);
  return Math.round(((longer.length - editDistance) / longer.length) * 100);
}

function levenshteinDistance(a: string, b: string): number {
  const matrix: number[][] = [];
  
  for (let i = 0; i <= b.length; i++) {
    matrix[i] = [i];
  }
  
  for (let j = 0; j <= a.length; j++) {
    matrix[0][j] = j;
  }
  
  for (let i = 1; i <= b.length; i++) {
    for (let j = 1; j <= a.length; j++) {
      if (b.charAt(i - 1) === a.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        );
      }
    }
  }
  
  return matrix[b.length][a.length];
}

// 候補検出（email/phone無しの場合のみ）
export function findDuplicateCandidates(
  currentRow: RowProcessed,
  currentIndex: number,
  allProcessedRows: RowProcessed[],
  threshold: number = 70
): DuplicateCandidate[] {
  const candidates: DuplicateCandidate[] = [];
  
  // email_norm または phone_norm があれば候補検出しない
  const hasEmailOrPhone = 
    (currentRow.normalized.email_norm && currentRow.normalized.email_norm.trim().length > 0) ||
    (currentRow.normalized.phone_norm && currentRow.normalized.phone_norm.trim().length > 0);
  
  if (hasEmailOrPhone) return candidates;
  
  const currentName = currentRow.normalized.full_name || '';
  const currentAddr1 = currentRow.normalized.address_line1 || '';
  
  if (!currentName) return candidates;
  
  // 既存行（自分より前の行）と比較
  for (let i = 0; i < currentIndex; i++) {
    const otherRow = allProcessedRows[i];
    const otherName = otherRow.normalized.full_name || '';
    const otherAddr1 = otherRow.normalized.address_line1 || '';
    
    if (!otherName) continue;
    
    const nameSim = similarity(currentName, otherName);
    const addrSim = currentAddr1 && otherAddr1 ? similarity(currentAddr1, otherAddr1) : 0;
    
    let score = 0;
    let matchType: DuplicateCandidate['matchType'] = 'name_only';
    let reason = '';
    
    if (nameSim >= 90 && addrSim >= 80) {
      score = Math.round((nameSim + addrSim) / 2);
      matchType = 'name_address';
      reason = `名前完全一致 + 住所類似 (name:${nameSim}, addr:${addrSim})`;
    } else if (nameSim >= 90) {
      score = nameSim;
      matchType = 'name_only';
      reason = `名前完全一致 (${nameSim})`;
    } else if (nameSim >= 70 && addrSim >= 70) {
      score = Math.round((nameSim + addrSim) / 2);
      matchType = 'name_address';
      reason = `名前類似 + 住所類似 (name:${nameSim}, addr:${addrSim})`;
    }
    
    if (score >= threshold) {
      candidates.push({
        candidateIndex: i,
        matchType,
        score,
        reason,
      });
    }
  }
  
  // スコア順にソート
  candidates.sort((a, b) => b.score - a.score);
  
  return candidates;
}

// 全行に対して候補検出
export function detectAllCandidates(
  processedRows: RowProcessed[],
  threshold: number = 70
): RowWithCandidates[] {
  return processedRows.map((row, index) => ({
    ...row,
    candidates: findDuplicateCandidates(row, index, processedRows, threshold),
  }));
}