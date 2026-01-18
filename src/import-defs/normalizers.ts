// src/import-defs/normalizers.ts
import type { NormalizerId } from "./types";

type EnumMapParams = {
  enum_map?: Record<string, string[]>;
  default?: string;
};

function toHalfWidth(str: string): string {
  // 全角英数を半角へ（住所・電話で効く）
  // 0xFF01-0xFF5E を -0xFEE0 で変換
  return str.replace(/[！-～]/g, (ch) =>
    String.fromCharCode(ch.charCodeAt(0) - 0xfee0)
  );
}

function normalizeHyphens(str: string): string {
  // 住所に混ざりがちなハイフン類を統一
  return str.replace(/[‐-‒–—―ー－−]/g, "-");
}

function collapseSpaces(str: string): string {
  // 全角スペースも含めて連続空白を1つに
  return str.replace(/[\s\u3000]+/g, " ").trim();
}

function digitsOnly(str: string): string {
  return str.replace(/[^\d]/g, "");
}

function enumMap(value: string, params?: EnumMapParams): string {
  const v = value.trim().toLowerCase();
  const map = params?.enum_map ?? {};
  for (const canonical of Object.keys(map)) {
    const aliases = map[canonical].map((x) => x.trim().toLowerCase());
    if (canonical.toLowerCase() === v) return canonical;
    if (aliases.includes(v)) return canonical;
  }
  return params?.default ?? value;
}

export function applyNormalizers(
  input: unknown,
  normalizers: NormalizerId[],
  normalizerParams?: Record<string, any>
): string {
  // すべて文字列として扱う（CSV/Excelは基本文字列）
  let value = input == null ? "" : String(input);

  for (const n of normalizers) {
    switch (n) {
      case "trim":
        value = value.trim();
        break;
      case "collapse_spaces":
        value = collapseSpaces(value);
        break;
      case "lower":
        value = value.toLowerCase();
        break;
      case "to_halfwidth":
        value = toHalfWidth(value);
        break;
      case "digits_only":
        value = digitsOnly(value);
        break;
      case "normalize_hyphens":
        value = normalizeHyphens(value);
        break;
      case "enum_map":
        value = enumMap(value, normalizerParams as any);
        break;
      default: {
        const _exhaustive: never = n;
        return _exhaustive;
      }
    }
  }

  return value;
}