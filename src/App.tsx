import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import ImportNewPage from "./pages/ImportNewPage";
import ImportWithS3 from "./pages/ImportWithS3";
import DuplicateResolution from "./pages/DuplicateResolution";

function App() {
  return (
    <BrowserRouter>
      <div>
        {/* ナビゲーション */}
        <div style={{ padding: "16px", borderBottom: "1px solid #ccc", display: "flex", gap: "16px" }}>
          <Link to="/" style={{ padding: "8px 16px", textDecoration: "none", color: "#007bff" }}>
            Lv3 (メモリ版)
          </Link>
          <Link to="/s3" style={{ padding: "8px 16px", textDecoration: "none", color: "#007bff" }}>
            Phase 5 (S3版)
          </Link>
        </div>

        {/* ルーティング */}
        <Routes>
          <Route path="/" element={<ImportNewPage />} />
          <Route path="/s3" element={<ImportWithS3 />} />
          <Route path="/duplicates/:importId" element={<DuplicateResolution />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;