// src/pages/ImportNewPage.tsx
import { useEffect, useMemo, useState } from "react";
import { loadImportDefinition } from "@/import-defs/loadDefinition";
import type { ImportDefinition } from "@/import-defs/types";
import { useFieldMapping, useImportPreviewValidation } from "@/import-defs/hooks";
import { parseCsvFile } from "@/import-csv/parseCsv";
import { parseXlsxFile } from "@/import-xlsx/parseXlsx";
import type { RowInput } from "@/import-defs/engine";

type Step = "upload" | "preview" | "mapping" | "validation" | "run";

function pickSampleValues(rows: RowInput[], col: string, n = 3): string[] {
  const out: string[] = [];
  for (const r of rows) {
    const v = r[col];
    const s = v == null ? "" : String(v);
    if (s.trim().length > 0) out.push(s);
    if (out.length >= n) break;
  }
  return out;
}

export default function ImportNewPage() {
  const [def, setDef] = useState<ImportDefinition | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);

  useEffect(() => {
    loadImportDefinition("/defs/customer_import_fields.v1.json")
      .then(setDef)
      .catch((e) => setParseError(String(e?.message ?? e)));
  }, []);

  if (!def) {
    return (
      <div style={{ padding: 16 }}>
        <h2>Import New</h2>
        <p>定義読み込み中...</p>
        {parseError && <p style={{ color: "crimson" }}>{parseError}</p>}
      </div>
    );
  }

  return <ImportNewBody def={def} />;
}

function ImportNewBody({ def }: { def: ImportDefinition }) {
  // file
  const [file, setFile] = useState<File | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);

  // parsed data
  const [columns, setColumns] = useState<string[]>([]);
  const [rows, setRows] = useState<RowInput[]>([]);

  // ui
  const [step, setStep] = useState<Step>("upload");
  const [previewLimit, setPreviewLimit] = useState(20);

  // run result (Lv1はローカルで「結果っぽい表示」)
  const [ran, setRan] = useState(false);

  const previewRows = useMemo(() => rows.slice(0, previewLimit), [rows, previewLimit]);

  // mapping / validation hooks
  const mappingHook = useFieldMapping(def, columns);
  const validationHook = useImportPreviewValidation(def, previewRows, mappingHook.mapping);

  const requiredUnmapped = mappingHook.requiredUnmapped ?? [];
  const errorSummary = validationHook.errorSummary ?? { errorRows: 0, byField: {} };

  const canGoPreview = !!file && columns.length > 0 && rows.length > 0;
  const canGoMapping = canGoPreview;
  const canGoValidation = canGoMapping && requiredUnmapped.length === 0;
  const canRun = canGoValidation;

  async function onDropFile(f: File) {
    setParseError(null);
    setRan(false);

    try {
      const name = f.name.toLowerCase();
      const isCsv = name.endsWith(".csv");
      const isXlsx = name.endsWith(".xlsx");

      if (!isCsv && !isXlsx) {
        throw new Error("CSV(.csv) か Excel(.xlsx) をアップロードしてください");
      }

      const result = isCsv ? await parseCsvFile(f) : await parseXlsxFile(f);

      if (result.columns.length === 0) throw new Error("ヘッダー行が見つかりませんでした");
      if (result.rows.length === 0) throw new Error("データ行が見つかりませんでした");

      setFile(f);
      setColumns(result.columns);
      setRows(result.rows);

      setStep("preview");
    } catch (e: any) {
      setParseError(e?.message ?? String(e));
      setFile(null);
      setColumns([]);
      setRows([]);
      setStep("upload");
    }
  }

  function onRun() {
    // Lv1: ローカルでバリデ結果を「実行」扱いにして、結果画面へ
    setRan(true);
    setStep("run");
  }

  return (
    <div style={{ padding: 16, display: "grid", gap: 16, maxWidth: 1100 }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h2 style={{ margin: 0 }}>顧客台帳インポート（Lv1）</h2>
          <div style={{ fontSize: 12, opacity: 0.7 }}>
            step: {step} / rows: {rows.length || 0}
          </div>
        </div>

        <nav style={{ display: "flex", gap: 8 }}>
          <button disabled={step === "upload"} onClick={() => setStep("upload")}>Upload</button>
          <button disabled={!canGoPreview} onClick={() => setStep("preview")}>Preview</button>
          <button disabled={!canGoMapping} onClick={() => setStep("mapping")}>Mapping</button>
          <button disabled={!canGoValidation} onClick={() => setStep("validation")}>Validation</button>
          <button disabled={!canRun} onClick={() => setStep("run")}>Run</button>
        </nav>
      </header>

      {/* Step 1: Upload */}
      {step === "upload" && (
        <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16 }}>
          <h3 style={{ marginTop: 0 }}>1) CSVをドラッグ＆ドロップ</h3>

          <Dropzone onFile={onDropFile} />

          <div style={{ marginTop: 12, fontSize: 12, opacity: 0.8 }}>
            ※ CSV(.csv) または Excel(.xlsx) 対応
          </div>

          {parseError && <p style={{ color: "crimson" }}>{parseError}</p>}
        </section>
      )}

      {/* Step 2: Preview */}
      {step === "preview" && (
        <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16 }}>
          <h3 style={{ marginTop: 0 }}>2) プレビュー</h3>

          <div style={{ display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
            <div><b>file:</b> {file?.name}</div>
            <div><b>columns:</b> {columns.length}</div>
            <div><b>rows:</b> {rows.length}</div>

            <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
              preview limit:
              <input
                type="number"
                min={5}
                max={100}
                value={previewLimit}
                onChange={(e) => setPreviewLimit(Number(e.target.value))}
                style={{ width: 80 }}
              />
            </label>

            <button onClick={() => setStep("mapping")} disabled={!canGoMapping}>
              次へ（Mapping）
            </button>
          </div>

          <PreviewTable columns={columns} rows={previewRows} />
        </section>
      )}

      {/* Step 3: Mapping */}
      {step === "mapping" && mappingHook && (
        <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16 }}>
          <h3 style={{ marginTop: 0 }}>3) 列マッピング</h3>

          {requiredUnmapped.length > 0 && (
            <div style={{ marginBottom: 12, color: "crimson" }}>
              必須未マップ: {requiredUnmapped.map((x) => x.label).join(", ")}
            </div>
          )}

          <ColumnMappingEditorUI
            def={def}
            detectedColumns={columns}
            previewRows={previewRows}
            mapping={mappingHook.mapping}
            onChange={mappingHook.setFieldMapping}
          />

          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <button onClick={() => setStep("preview")}>戻る（Preview）</button>
            <button onClick={() => setStep("validation")} disabled={!canGoValidation}>
              次へ（Validation）
            </button>
          </div>
        </section>
      )}

      {/* Step 4: Validation */}
      {step === "validation" && validationHook && (
        <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16 }}>
          <h3 style={{ marginTop: 0 }}>4) バリデーション（プレビュー行）</h3>

          <div style={{ display: "flex", gap: 16, flexWrap: "wrap", alignItems: "center" }}>
            <div><b>error rows:</b> {errorSummary.errorRows} / {previewRows.length}</div>
            <button onClick={onRun} disabled={!canRun}>
              Run（ローカル実行）
            </button>
          </div>

          <ValidationSummaryUI def={def} byField={errorSummary.byField} />

          <ErrorRowsTable results={validationHook.results} />
        </section>
      )}

      {/* Step 5: Run (Lv1) */}
      {step === "run" && validationHook && (
        <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16 }}>
          <h3 style={{ marginTop: 0 }}>5) Run 結果（Lv1: ローカル）</h3>

          {!ran ? (
            <p>まだ実行されていません</p>
          ) : (
            <>
              <p style={{ opacity: 0.8 }}>
                Lv1ではDB登録はせず、バリデ結果から「取り込み結果っぽい集計」を表示します。
              </p>

              <RunResultMock results={validationHook.results} />

              <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                <button onClick={() => setStep("mapping")}>戻る（Mapping）</button>
                <button onClick={() => setStep("validation")}>戻る（Validation）</button>
              </div>
            </>
          )}
        </section>
      )}
    </div>
  );
}

/** --------------- UI Parts (最小) --------------- */

function Dropzone({ onFile }: { onFile: (file: File) => void }) {
  const [isOver, setIsOver] = useState(false);

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsOver(true);
      }}
      onDragLeave={() => setIsOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsOver(false);
        const f = e.dataTransfer.files?.[0];
        if (f) onFile(f);
      }}
      style={{
        border: "2px dashed #aaa",
        borderRadius: 12,
        padding: 24,
        textAlign: "center",
        background: isOver ? "#f5f5f5" : "transparent",
      }}
    >
      <p style={{ margin: 0 }}>ここにCSV/Excelをドロップ</p>
      <p style={{ margin: "8px 0 0", fontSize: 12, opacity: 0.7 }}>
        または input から選択
      </p>

      <input
        type="file"
        accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
        }}
        style={{ marginTop: 12 }}
      />
    </div>
  );
}

function PreviewTable({
  columns,
  rows,
}: {
  columns: string[];
  rows: Record<string, unknown>[];
}) {
  return (
    <div style={{ overflowX: "auto", marginTop: 12 }}>
      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c} style={{ borderBottom: "1px solid #ddd", textAlign: "left", padding: 8 }}>
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              {columns.map((c) => (
                <td key={c} style={{ borderBottom: "1px solid #f0f0f0", padding: 8, fontSize: 12 }}>
                  {String(r[c] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ColumnMappingEditorUI({
  def,
  detectedColumns,
  previewRows,
  mapping,
  onChange,
}: {
  def: ImportDefinition;
  detectedColumns: string[];
  previewRows: RowInput[];
  mapping: Record<string, string>;
  onChange: (fieldKey: string, sourceColumnName: string) => void;
}) {
  return (
    <div style={{ display: "grid", gap: 10 }}>
      {def.fields.map((f) => {
        const mappedCol = mapping[f.key] ?? "";
        const samples = mappedCol ? pickSampleValues(previewRows, mappedCol) : [];

        return (
          <div
            key={f.key}
            style={{
              display: "grid",
              gridTemplateColumns: "220px 260px 1fr",
              gap: 12,
              alignItems: "center",
              padding: 10,
              border: "1px solid #eee",
              borderRadius: 10,
            }}
          >
            <div>
              <div style={{ fontWeight: 700 }}>
                {f.label} {f.required ? <span style={{ color: "crimson" }}>*</span> : null}
              </div>
              <div style={{ fontSize: 12, opacity: 0.7 }}>{f.ui?.hint ?? f.key}</div>
            </div>

            <select
              value={mappedCol}
              onChange={(e) => onChange(f.key, e.target.value)}
              style={{ padding: 8 }}
            >
              <option value="">（未選択）</option>
              {detectedColumns.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>

            <div style={{ fontSize: 12, opacity: 0.8 }}>
              {samples.length > 0 ? (
                <>
                  <div style={{ fontWeight: 700 }}>samples:</div>
                  <div>{samples.join(" / ")}</div>
                </>
              ) : (
                <div>samples: -</div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function ValidationSummaryUI({
  def,
  byField,
}: {
  def: ImportDefinition;
  byField: Record<string, number>;
}) {
  const rows = def.fields
    .map((f) => ({
      key: f.key,
      label: f.label,
      count: byField[f.key] ?? 0,
    }))
    .filter((x) => x.count > 0)
    .sort((a, b) => b.count - a.count);

  if (rows.length === 0) return <p style={{ marginTop: 12 }}>エラーなし（プレビュー範囲）</p>;

  return (
    <div style={{ marginTop: 12 }}>
      <h4 style={{ margin: "8px 0" }}>フィールド別エラー件数</h4>
      <ul style={{ margin: 0, paddingLeft: 18 }}>
        {rows.map((r) => (
          <li key={r.key}>
            {r.label}: {r.count}
          </li>
        ))}
      </ul>
    </div>
  );
}

function ErrorRowsTable({
  results,
}: {
  results: Array<{
    raw: RowInput;
    normalized: Record<string, string>;
    errors: Array<{ fieldKey: string; fieldLabel: string; code: string; message: string }>;
  }>;
}) {
  const errorRows = results
    .map((r, idx) => ({ idx, ...r }))
    .filter((r) => r.errors.length > 0)
    .slice(0, 20);

  if (errorRows.length === 0) return null;

  return (
    <div style={{ marginTop: 12 }}>
      <h4 style={{ margin: "8px 0" }}>エラー行（先頭20件）</h4>
      <div style={{ overflowX: "auto" }}>
        <table style={{ borderCollapse: "collapse", width: "100%" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: 8 }}>#</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: 8 }}>errors</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: 8 }}>normalized (partial)</th>
            </tr>
          </thead>
          <tbody>
            {errorRows.map((r) => (
              <tr key={r.idx}>
                <td style={{ borderBottom: "1px solid #f0f0f0", padding: 8 }}>{r.idx + 1}</td>
                <td style={{ borderBottom: "1px solid #f0f0f0", padding: 8, fontSize: 12 }}>
                  <ul style={{ margin: 0, paddingLeft: 18 }}>
                    {r.errors.map((e, i) => (
                      <li key={i}>
                        [{e.fieldLabel}] {e.message}
                      </li>
                    ))}
                  </ul>
                </td>
                <td style={{ borderBottom: "1px solid #f0f0f0", padding: 8, fontSize: 12 }}>
                  <code>
                    {JSON.stringify(
                      {
                        full_name: r.normalized["full_name"],
                        email: r.normalized["email"],
                        phone: r.normalized["phone"],
                        registered_at: r.normalized["registered_at"],
                      },
                      null,
                      0
                    )}
                  </code>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function RunResultMock({
  results,
}: {
  results: Array<{ errors: any[]; normalized: Record<string, string> }>;
}) {
  // Lv1: errorsがない行を「inserted」扱いにして雰囲気を作る
  const ok = results.filter((r) => r.errors.length === 0).length;
  const ng = results.length - ok;

  return (
    <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginTop: 12 }}>
      <Stat label="preview rows" value={results.length} />
      <Stat label="inserted (mock)" value={ok} />
      <Stat label="error (mock)" value={ng} />
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ border: "1px solid #eee", borderRadius: 10, padding: 12, minWidth: 160 }}>
      <div style={{ fontSize: 12, opacity: 0.7 }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 800 }}>{value}</div>
    </div>
  );
}