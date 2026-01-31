# Customer Import System

顧客データCSVの自動インポート・重複検知・解決システム

## 📋 概要

CSV/Excelファイルからの顧客データインポートにおける実務課題（表記ゆれ、重複データ、大容量ファイル）を解決するWebアプリケーション。

## ✨ 主要機能

### 1. S3直接アップロード
- presigned URLによるフロントエンドからの直接アップロード
- バックエンド負荷の削減とスケーラビリティの確保

### 2. 自動重複検知
- **完全一致**: email/phone完全一致 → 既存顧客を自動更新
- **類似度検知**: Levenshtein距離による名前の類似判定 → 手動解決候補へ

### 3. 重複解決UI
- 既存顧客と新規データの比較表示
- 3つのアクション選択
  - **マージ**: 既存顧客データを新規データで更新
  - **新規作成**: 別顧客として新規登録
  - **無視**: スキップ

### 4. バックグラウンド処理
- FastAPI BackgroundTasksによる非同期処理
- 大量データ対応（20件/約3秒）

## 🛠️ 技術スタック

### Frontend
- React 18 + TypeScript
- Vite (ビルドツール)
- TailwindCSS

### Backend
- FastAPI (Python 3.11)
- SQLAlchemy (ORM)
- MySQL 8.0
- boto3 (AWS SDK)

### Infrastructure
- Docker + Docker Compose
- AWS S3 (ファイルストレージ)

### アルゴリズム
- Levenshtein距離（文字列類似度計算）

## 🚀 セットアップ

### 前提条件
- Docker Desktop
- Node.js 20+
- AWS アカウント（S3バケット作成済み）

### 1. リポジトリクローン
```bash
git clone https://github.com/tk53582005/customer-import.git
cd customer-import
```

### 2. 環境変数設定
```bash
# backend/.env を作成
cat > backend/.env <<EOF
DATABASE_URL=mysql+pymysql://app:app_pass@mysql:3306/customer_import?charset=utf8mb4
CORS_ORIGINS=http://localhost:5173
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-northeast-1
AWS_S3_BUCKET=your_bucket_name
EOF
```

### 3. 起動
```bash
# バックエンド（Docker）
docker compose up -d

# フロントエンド
npm install
npm run dev
```

### 4. アクセス
- フロントエンド: http://localhost:5173
- バックエンドAPI: http://localhost:8000/docs

## 📊 システム構成
```
┌─────────────┐   presigned URL   ┌──────┐
│ React App   │ ─────────────────>│  S3  │
└─────────────┘                    └──────┘
       │                              │
       │ インポート指令               │ ダウンロード
       ▼                              ▼
┌─────────────┐                 ┌──────────┐
│  FastAPI    │ ───────────────>│  MySQL   │
└─────────────┘   CRUD操作      └──────────┘
```

## 🎯 実装フェーズ

- ✅ Phase 1-3: 基礎機能（ファイルアップロード、バリデーション）
- ✅ Phase 4: 重複検知・解決UI
- ✅ Phase 5: S3直接アップロード + バックグラウンド処理

## 🔒 セキュリティ

- `.env` ファイルの完全隔離（.gitignore + .git/info/exclude）
- pre-pushフックによる機密情報漏洩防止
- AWS presigned URLによる時限式アップロード権限

## 📝 サンプルデータ

CSVフォーマット例：
```csv
顧客名,TEL,Mail
山田 太郎,090-1234-5678,taro.yamada@example.com
```

## 🤝 開発者

[@tk53582005](https://github.com/tk53582005)

## 📄 ライセンス

MIT License

## 🧪 テスト
```bash
# ローカル環境
cd backend
python -m pytest tests/ -v

# Docker環境（推奨）
docker compose exec backend pytest tests/ -v
```

**注意**: DB接続が必要なテストはDocker環境での実行を推奨
