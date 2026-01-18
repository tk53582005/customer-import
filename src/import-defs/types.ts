// src/import-defs/types.ts
import { z } from "zod";

export const FieldTypeSchema = z.enum(["string", "email", "tel", "date", "enum"]);

export const ValidatorRuleSchema = z.enum([
  "min_length",
  "max_length",
  "email_format",
  "phone_jp_len",
  "enum_one_of",
  "date_parseable",
]);

export const NormalizerIdSchema = z.enum([
  "trim",
  "collapse_spaces",
  "lower",
  "to_halfwidth",
  "digits_only",
  "normalize_hyphens",
  "enum_map",
]);

export const ValidatorSchema = z.object({
  rule: ValidatorRuleSchema,
  params: z.record(z.string(), z.any()).default({}),
});

export const EnumOptionSchema = z.object({
  value: z.string(),
  label: z.string(),
});

export const FieldUiSchema = z
  .object({
    hint: z.string().optional(),
    placeholder: z.string().optional(),
    options: z.array(EnumOptionSchema).optional(), // for enum
  })
  .default({});

export const FieldDefinitionSchema = z.object({
  key: z.string(),
  label: z.string(),
  required: z.boolean(),
  type: FieldTypeSchema,
  ui: FieldUiSchema.optional(),

  normalizers: z.array(NormalizerIdSchema).default([]),

  // normalizer_params はフィールドごとに必要な場合だけ利用
  normalizer_params: z.record(z.string(), z.any()).optional(),

  validators: z.array(ValidatorSchema).default([]),
});

export const ComputedFieldSchema = z.object({
  key: z.string(),
  from: z.string(),
  normalizers: z.array(NormalizerIdSchema).default([]),
});

export const DedupePolicySchema = z.object({
  priority_keys: z.array(z.string()).default([]),
  candidate_rule: z
    .object({
      when_missing_all: z.array(z.string()).default([]),
      match_keys: z.array(z.string()).default([]),
      threshold: z.number().int().min(0).max(100).default(70),
    })
    .optional(),
});

export const ImportDefinitionSchema = z.object({
  schema_version: z.string(),
  entity: z.string(),
  fields: z.array(FieldDefinitionSchema),
  computed_fields: z.array(ComputedFieldSchema).default([]),
  dedupe_policy: DedupePolicySchema.optional(),
});

export type FieldType = z.infer<typeof FieldTypeSchema>;
export type NormalizerId = z.infer<typeof NormalizerIdSchema>;
export type ValidatorRule = z.infer<typeof ValidatorRuleSchema>;

export type Validator = z.infer<typeof ValidatorSchema>;
export type FieldDefinition = z.infer<typeof FieldDefinitionSchema>;
export type ComputedField = z.infer<typeof ComputedFieldSchema>;
export type DedupePolicy = z.infer<typeof DedupePolicySchema>;
export type ImportDefinition = z.infer<typeof ImportDefinitionSchema>;

// mapping: Excel列 -> target field key
export type FieldMapping = Record<string /* fieldKey */, string /* sourceColumnName */>;