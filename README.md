# docs-checker

メール本文の誤字・敬語チェックを AI で行う社内向けアプリ。

## 構成

- `docs/` — 設計ドキュメント（`architecture.md`、phase ごとの記録）
- `backend/` — FastAPI + SQLAlchemy + Gemini（uv 管理）
- `frontend/` — SvelteKit SPA + Tailwind + shadcn-svelte（bun 管理）
- `backend/docker/compose.yml` — PostgreSQL

## セットアップ（phase 1 時点）

```bash
# DB を起動
cd backend && docker compose -f docker/compose.yml up -d

# backend
uv sync
uv run pytest               # スモークテスト
uv run uvicorn api.app:app --reload

# frontend（別ターミナル）
cd frontend
bun install
bun run dev
```

## 進捗

- [x] phase 1: プロジェクト初期化（`docs/phase-1.md`）
- [ ] phase 2: DB + 認証
- [ ] phase 3: 校正 API
- [ ] phase 4: フロント
- [ ] phase 5: 管理者機能
