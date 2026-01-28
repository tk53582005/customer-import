import { useState } from "react";
import ImportNewPage from "./pages/ImportNewPage";
import ImportWithS3 from "./pages/ImportWithS3";

function App() {
  const [page, setPage] = useState<"lv3" | "s3">("lv3");

  return (
    <div>
      {/* ページ切り替えボタン */}
      <div style={{ padding: "16px", borderBottom: "1px solid #ccc", display: "flex", gap: "8px" }}>
        <button
          onClick={() => setPage("lv3")}
          style={{
            padding: "8px 16px",
            backgroundColor: page === "lv3" ? "#007bff" : "#f0f0f0",
            color: page === "lv3" ? "white" : "black",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer"
          }}
        >
          Lv3 (メモリ版)
        </button>
        <button
          onClick={() => setPage("s3")}
          style={{
            padding: "8px 16px",
            backgroundColor: page === "s3" ? "#007bff" : "#f0f0f0",
            color: page === "s3" ? "white" : "black",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer"
          }}
        >
          Phase 2 (S3版)
        </button>
      </div>

      {/* ページ表示 */}
      {page === "lv3" ? <ImportNewPage /> : <ImportWithS3 />}
    </div>
  );
}

export default App;