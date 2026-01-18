// src/import-defs/loadDefinition.ts
import { ImportDefinitionSchema, type ImportDefinition } from "./types";

export async function loadImportDefinition(url: string): Promise<ImportDefinition> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to load definition: ${res.status}`);
  const json = await res.json();

  const parsed = ImportDefinitionSchema.safeParse(json);
  if (!parsed.success) {
    throw new Error(`Definition schema invalid: ${parsed.error.message}`);
  }
  return parsed.data;
}