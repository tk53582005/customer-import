import { useState, useRef } from "react";

interface UploadStatus {
  phase: "idle" | "uploading" | "processing" | "completed" | "error";
  progress: number;
  message: string;
}

interface PresignedUrlResponse {
  upload_url: string;
  s3_key: string;
  expires_in: number;
}

interface ImportFromS3Response {
  job_id: string;
  status: string;
  message: string;
}

export default function ImportWithS3() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [status, setStatus] = useState<UploadStatus>({
    phase: "idle",
    progress: 0,
    message: "",
  });
  const [jobId, setJobId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.name.endsWith(".csv")) {
        setStatus({
          phase: "error",
          progress: 0,
          message: "CSVファイルを選択してください",
        });
        return;
      }
      setSelectedFile(file);
      setStatus({
        phase: "idle",
        progress: 0,
        message: `選択: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`,
      });
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      // Step 1: presigned URL取得
      setStatus({ phase: "uploading", progress: 10, message: "アップロード準備中..." });

      const presignedResponse = await fetch("http://localhost:8000/api/customers/upload/presigned-url", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          filename: selectedFile.name,
          content_type: "text/csv",
        }),
      });

      if (!presignedResponse.ok) {
        throw new Error("presigned URL の取得に失敗しました");
      }

      const { upload_url, s3_key }: PresignedUrlResponse = await presignedResponse.json();

      // Step 2: S3へアップロード
      setStatus({ phase: "uploading", progress: 30, message: "S3へアップロード中..." });

      const uploadResponse = await fetch(upload_url, {
        method: "PUT",
        headers: {
          "Content-Type": "text/csv",
        },
        body: selectedFile,
      });

      if (!uploadResponse.ok) {
        throw new Error("S3へのアップロードに失敗しました");
      }

      setStatus({ phase: "uploading", progress: 60, message: "アップロード完了！" });

      // Step 3: インポート実行依頼
      setStatus({ phase: "processing", progress: 70, message: "インポート処理を開始中..." });

      const importResponse = await fetch("http://localhost:8000/api/customers/upload/import-from-s3", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          s3_key: s3_key,
        }),
      });

      if (!importResponse.ok) {
        throw new Error("インポート実行の依頼に失敗しました");
      }

      const importResult: ImportFromS3Response = await importResponse.json();
      setJobId(importResult.job_id);

      setStatus({ phase: "processing", progress: 90, message: importResult.message });

      // 仮の完了処理（TODO: 実際はポーリングでステータス確認）
      setTimeout(() => {
        setStatus({
          phase: "completed",
          progress: 100,
          message: `✅ インポート完了！ジョブID: ${importResult.job_id}`,
        });
      }, 2000);
    } catch (error) {
      setStatus({
        phase: "error",
        progress: 0,
        message: error instanceof Error ? error.message : "エラーが発生しました",
      });
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setJobId(null);
    setStatus({ phase: "idle", progress: 0, message: "" });
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div style={{ padding: "24px", maxWidth: "800px", margin: "0 auto" }}>
      <h1>🚀 Phase 5: S3直接アップロード</h1>

      {/* ファイル選択エリア */}
      <div
        style={{
          border: "2px dashed #ccc",
          borderRadius: "8px",
          padding: "32px",
          textAlign: "center",
          marginBottom: "24px",
          backgroundColor: status.phase === "error" ? "#fff5f5" : "#f9f9f9",
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          onChange={handleFileSelect}
          style={{ display: "none" }}
          id="file-input"
        />
        <label
          htmlFor="file-input"
          style={{
            display: "inline-block",
            padding: "12px 24px",
            backgroundColor: "#007bff",
            color: "white",
            borderRadius: "4px",
            cursor: "pointer",
            marginBottom: "16px",
          }}
        >
          📁 CSVファイルを選択
        </label>
        {selectedFile && (
          <div style={{ marginTop: "16px", color: "#333" }}>
            <strong>{selectedFile.name}</strong>
            <br />
            <span style={{ fontSize: "14px", color: "#666" }}>
              {(selectedFile.size / 1024).toFixed(1)} KB
            </span>
          </div>
        )}
      </div>

      {/* ステータス表示 */}
      {status.message && (
        <div
          style={{
            padding: "16px",
            borderRadius: "4px",
            marginBottom: "24px",
            backgroundColor:
              status.phase === "error"
                ? "#fee"
                : status.phase === "completed"
                ? "#efe"
                : "#e3f2fd",
            color:
              status.phase === "error"
                ? "#c00"
                : status.phase === "completed"
                ? "#0a0"
                : "#1976d2",
          }}
        >
          {status.message}
        </div>
      )}

      {/* プログレスバー */}
      {status.phase !== "idle" && status.phase !== "error" && (
        <div style={{ marginBottom: "24px" }}>
          <div
            style={{
              width: "100%",
              height: "8px",
              backgroundColor: "#e0e0e0",
              borderRadius: "4px",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                width: `${status.progress}%`,
                height: "100%",
                backgroundColor: "#007bff",
                transition: "width 0.3s ease",
              }}
            />
          </div>
          <div style={{ textAlign: "center", marginTop: "8px", fontSize: "14px", color: "#666" }}>
            {status.progress}%
          </div>
        </div>
      )}

      {/* アクションボタン */}
      <div style={{ display: "flex", gap: "12px" }}>
        <button
          onClick={handleUpload}
          disabled={!selectedFile || status.phase === "uploading" || status.phase === "processing"}
          style={{
            flex: 1,
            padding: "12px 24px",
            backgroundColor:
              !selectedFile || status.phase === "uploading" || status.phase === "processing"
                ? "#ccc"
                : "#28a745",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor:
              !selectedFile || status.phase === "uploading" || status.phase === "processing"
                ? "not-allowed"
                : "pointer",
            fontSize: "16px",
            fontWeight: "bold",
          }}
        >
          {status.phase === "uploading"
            ? "アップロード中..."
            : status.phase === "processing"
            ? "処理中..."
            : "🚀 アップロード開始"}
        </button>

        {(status.phase === "completed" || status.phase === "error") && (
          <button
            onClick={handleReset}
            style={{
              padding: "12px 24px",
              backgroundColor: "#6c757d",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "16px",
            }}
          >
            リセット
          </button>
        )}
      </div>

      {/* デバッグ情報 */}
      <details style={{ marginTop: "32px", fontSize: "12px", color: "#666" }}>
        <summary style={{ cursor: "pointer" }}>デバッグ情報</summary>
        <pre style={{ backgroundColor: "#f5f5f5", padding: "12px", borderRadius: "4px", overflow: "auto" }}>
          {JSON.stringify({ selectedFile: selectedFile?.name, jobId, status }, null, 2)}
        </pre>
      </details>
    </div>
  );
}
