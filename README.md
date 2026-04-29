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
PR コメントで `@claude` をメンションすると追加レビュー / 質問対応もしてくれる。

#### 初回セットアップ（リポジトリごとに1回）

**1. Claude Code GitHub App をインストール**

<https://github.com/apps/claude> から `hyeon0620/docs-checker` にインストール。
これが無いと workflow 実行時に `Claude Code is not installed on this repository` エラーで落ちる。

**2. OAuth トークンを生成**

ローカルの Claude Code CLI で：

```bash
claude setup-token
```

`sk-ant-oat01-...` のような長寿命トークンが表示される。
**Claude Code Plan / Pro / Max を契約していれば API キー不要**で、Plan の枠から消費される。

**3. GitHub Secret に登録**

リポジトリの Settings → Secrets and variables → Actions → **New repository secret**

- Name: `CLAUDE_CODE_OAUTH_TOKEN`
- Value: 上で取得したトークン

#### トラブル時の確認

- `Claude Code is not installed` → 上記 1 の App インストール忘れ
- 認証エラー → 上記 2 のトークンを再発行して 3 を更新
- 動かない → Actions タブから **Re-run failed jobs** で再実行
