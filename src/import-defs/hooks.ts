// src/import-defs/hooks.ts
import { useCallback, useMemo, useState } from "react";
import type { ImportDefinition, FieldMapping } from "./types";
import type { RowInput, RowProcessed } from "./engine";
import { validateRow } from "./engine";

export function useFieldMapping(def: ImportDefinition, detectedColumns: string[]) {
  const [mapping, setMapping] = useState<FieldMapping>(() => {
    const m: FieldMapping = {};
    for (const f of def.fields) {
      const exact = detectedColumns.find((c) => c === f.label || c === f.key);
      if (exact) {
        m[f.key] = exact;
        continue;
      }
      const partial = detectedColumns.find((c) => c.includes(f.label));
      if (partial) m[f.key] = partial;
    }
    return m;
  });

  const setFieldMapping = useCallback((fieldKey: string, sourceColumnName: string) => {
    setMapping((prev) => ({ ...prev, [fieldKey]: sourceColumnName }));
  }, []);

  const clearFieldMapping = useCallback((fieldKey: string) => {
    setMapping((prev) => {
      const next = { ...prev };
      delete next[fieldKey];
      return next;
    });
  }, []);

  const requiredUnmapped = useMemo(() => {
    return def.fields
      .filter((f) => f.required)
      .filter((f) => !mapping[f.key] || mapping[f.key].trim() === "")
      .map((f) => ({ key: f.key, label: f.label }));
  }, [def.fields, mapping]);

  return {
    mapping,
    setFieldMapping,
    clearFieldMapping,
    requiredUnmapped,
  };
}

export function useImportPreviewValidation(
  def: ImportDefinition,
  previewRows: RowInput[],
  mapping: FieldMapping
) {
  const results: RowProcessed[] = useMemo(() => {
    return previewRows.map((r) => validateRow(r, mapping, def));
  }, [def, previewRows, mapping]);

  const errorSummary = useMemo(() => {
    let errorRows = 0;
    const byField: Record<string, number> = {};
    for (const r of results) {
      if (r.errors.length > 0) errorRows += 1;
      for (const e of r.errors) {
        byField[e.fieldKey] = (byField[e.fieldKey] ?? 0) + 1;
      }
    }
    return { errorRows, byField };
  }, [results]);

  return { results, errorSummary };
}