// src/import-defs/validators.ts
import type { Validator, FieldDefinition } from "./types";

type ValidationError = {
  fieldKey: string;
  fieldLabel: string;
  code: string;
  message: string;
};

export type RowValidationResult = {
  ok: boolean;
  errors: ValidationError[];
};

function isBlank(v: string): boolean {
  return v.trim().length === 0;
}

function isValidEmail(v: string): boolean {
  // 厳密すぎない実務寄り（Lv1用）
  // 空白は事前にtrimされる想定
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
}

function parseDateLoose(v: string, formats: string[]): Date | null {
  // 対応: YYYY/MM/DD or YYYY-MM-DD
  const s = v.trim();
  if (!s) return null;

  for (const f of formats) {
    if (f === "YYYY/MM/DD") {
      const m = /^(\d{4})\/(\d{1,2})\/(\d{1,2})$/.exec(s);
      if (!m) continue;
      const y = Number(m[1]);
      const mo = Number(m[2]);
      const d = Number(m[3]);
      const dt = new Date(y, mo - 1, d);
      if (dt.getFullYear() === y && dt.getMonth() === mo - 1 && dt.getDate() === d) return dt;
    }
    if (f === "YYYY-MM-DD") {
      const m = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(s);
      if (!m) continue;
      const y = Number(m[1]);
      const mo = Number(m[2]);
      const d = Number(m[3]);
      const dt = new Date(y, mo - 1, d);
      if (dt.getFullYear() === y && dt.getMonth() === mo - 1 && dt.getDate() === d) return dt;
    }
  }
  return null;
}

export function validateValue(
  field: FieldDefinition,
  value: string
): ValidationError[] {
  const errs: ValidationError[] = [];
  const label = field.label;

  // required check
  if (field.required && isBlank(value)) {
    errs.push({
      fieldKey: field.key,
      fieldLabel: label,
      code: "required",
      message: `${label}は必須です`,
    });
    // requiredエラーならこれ以上の検証は不要でもOK
    return errs;
  }

  // optional blank -> OK
  if (!field.required && isBlank(value)) return errs;

  for (const v of field.validators ?? []) {
    const rule = v.rule;
    const params = v.params ?? {};

    switch (rule) {
      case "min_length": {
        const min = Number(params.value ?? 0);
        if (value.length < min) {
          errs.push({
            fieldKey: field.key,
            fieldLabel: label,
            code: "min_length",
            message: `${label}は${min}文字以上にしてください`,
          });
        }
        break;
      }
      case "max_length": {
        const max = Number(params.value ?? 999999);
        if (value.length > max) {
          errs.push({
            fieldKey: field.key,
            fieldLabel: label,
            code: "max_length",
            message: `${label}は${max}文字以内にしてください`,
          });
        }
        break;
      }
      case "email_format": {
        if (!isValidEmail(value)) {
          errs.push({
            fieldKey: field.key,
            fieldLabel: label,
            code: "email_format",
            message: `${label}の形式が不正です`,
          });
        }
        break;
      }
      case "phone_jp_len": {
        const min = Number(params.min ?? 9);
        const max = Number(params.max ?? 11);
        if (value.length < min || value.length > max) {
          errs.push({
            fieldKey: field.key,
            fieldLabel: label,
            code: "phone_len",
            message: `${label}は${min}〜${max}桁の数字にしてください`,
          });
        }
        break;
      }
      case "enum_one_of": {
        const values: string[] = params.values ?? [];
        if (!values.includes(value)) {
          errs.push({
            fieldKey: field.key,
            fieldLabel: label,
            code: "enum_one_of",
            message: `${label}が不正です（許可: ${values.join(", ")}）`,
          });
        }
        break;
      }
      case "date_parseable": {
        const formats: string[] = params.formats ?? ["YYYY/MM/DD", "YYYY-MM-DD"];
        const dt = parseDateLoose(value, formats);
        if (!dt) {
          errs.push({
            fieldKey: field.key,
            fieldLabel: label,
            code: "date_parseable",
            message: `${label}の日付形式が不正です`,
          });
        }
        break;
      }
      default: {
        const _exhaustive: never = rule;
        return errs;
      }
    }
  }

  return errs;
}