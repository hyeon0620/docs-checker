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
uv run uvicorn api.main:app --reload

# frontend（別ターミナル）
cd frontend
bun install
bun run dev
```

## 進捗

- [x] phase 1: プロジェクト初期化（`docs/phase-1.md`）
- [x] phase 2: DB + 認証（`docs/phase-2.md`）
- [x] phase 3: 校正 API（`docs/phase-3.md`）
- [ ] phase 4: フロント
- [ ] phase 5: 管理者機能

## 開発フロー

### Git フック（lefthook）

`pre-commit` で lint / format 確認、`pre-push` で全テストを走らせる。

```bash
# インストール（初回のみ）
brew install lefthook
lefthook install

# 一時的にバイパス
LEFTHOOK=0 git commit -m "..."
git push --no-verify
```

### PR レビュー（GitHub Actions）

`develop` / `main` 宛に PR を出すと、Claude による自動レビューが走る（`.github/workflows/pr-review.yml`）。

**初回セットアップ**：GitHub リポジトリの Settings → Secrets and variables → Actions に `CLAUDE_CODE_OAUTH_TOKEN` を追加する必要がある。

PR コメントで `@claude` をメンションすると追加レビュー / 質問対応もしてくれる。
