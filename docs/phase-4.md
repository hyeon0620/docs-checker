---
title: "フロントエンド フェーズ"
---

# フロントエンド フェーズ

SvelteKit + shadcn-svelte によるブラウザ UI の実装

Hyonun Kin

2026-04-29

## 目的・背景

phase 3 までで API 側は完成（`/api/login` `/api/me` `/api/logout` `/api/correct`）。本フェーズではユーザーがブラウザで使える UI を完成させる。

設計方針：

- **pure SPA**：バックエンドは API のみで HTML を返さない設計に合わせ、`+layout.ts` で `ssr = false`
- **Cookie 認証のみ**：フロント側で JWT を保持しない（HttpOnly Cookie 任せ）。`credentials: 'include'` で送信
- **shadcn-svelte（vega style + zinc base）+ Tailwind v4**
- **ログイン状態の管理**：Svelte 5 runes ベースのクラス。token は持たず user 情報だけ
- 校正結果は永続化しない方針通り `/` 内に直接表示

ptw-respec の `frontend/src/lib/stores/auth.svelte.ts` を参考にしつつ、OAuth / refresh token / context API などの過剰な抽象は削ぎ落とした。

## 要件

機能要件：

- ユーザーが `/login` で ID / パスワードを入力してログインできる
- ログイン済みなら `/` で textarea にメール本文を貼って校正できる
- 結果は同画面に表示（スコア + 修正後 + 指摘事項）
- 右上のログアウトボタンでセッション破棄
- 未認証時は自動で `/login` にリダイレクト

非機能要件：

- フロント `:5173` ↔ バックエンド `:8000` のオリジン違いで Cookie が通る（CORS 設定）
- `bun run check` （TypeScript / Svelte 型チェック）が 0 エラー
- `bun run build` が成功

## 設計

### 認証フロー

```
[初回アクセス]
  Browser: GET /
    ↓ +layout の onMount で authStore.init()
  authStore: GET /api/me (Cookie 同梱)
    ├─ 200 → user に保存、isAuthenticated = true
    └─ 401 → user = null、$effect が /login へリダイレクト

[ログイン]
  /login で submit
    ↓ authStore.login(u, p)
  POST /api/login → サーバが Set-Cookie: token=...; HttpOnly
  user 状態を更新 → goto('/')

[ログアウト]
  ヘッダの「ログアウト」クリック
    ↓ authStore.logout()
  POST /api/logout → サーバが Cookie 削除
  user = null → goto('/login')
```

### CORS（バックエンド）

```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,        # Cookie 跨ぎに必須
    allow_methods=["*"],
    allow_headers=["*"],
)
```

`allow_credentials=True` の時 `allow_origins=["*"]` は使えない仕様なので、`config.py` で明示的に origin を読む。

### ファイル構成

```
docs-checker/
├── backend/
│   └── api/
│       ├── config.py          # allowed_origins / cors_origins 追加
│       └── main.py            # CORSMiddleware
└── frontend/
    ├── components.json        # shadcn-svelte 設定（手書き）
    ├── src/
    │   ├── lib/
    │   │   ├── api.ts         # fetch ラッパ + 各エンドポイント関数
    │   │   ├── utils.ts       # cn, WithElementRef, WithoutChildren
    │   │   ├── stores/
    │   │   │   └── auth.svelte.ts  # AuthStore クラス
    │   │   └── components/ui/      # shadcn-svelte コンポーネント
    │   └── routes/
    │       ├── +layout.ts     # ssr=false, prerender=false
    │       ├── +layout.svelte # 認証ガード + ヘッダ
    │       ├── +page.svelte   # / 校正画面
    │       ├── login/
    │       │   └── +page.svelte
    │       └── layout.css     # tailwind + shadcn テーマ変数
    └── .env.example           # VITE_API_URL
```

### shadcn-svelte 導入での詰まり

CLI v1.2.7 は `--preset` に **encoded code** を要求する設計に変わっており、`vega` `nova` 等の素のキーでは弾かれる（preset を shadcn-svelte.com/create で作って URL から code を取得する想定）。

回避策：`components.json` を手書きしてから `add` だけ動かす。`init` は通さない。

```json
{
    "$schema": "https://next.shadcn-svelte.com/schema.json",
    "style": "vega",
    "tailwind": {
        "css": "src/routes/layout.css",
        "baseColor": "zinc"
    },
    "aliases": { ... },
    "typescript": true,
    "iconLibrary": "lucide"
}
```

これで `bunx shadcn-svelte@latest add button card input ...` が想定通りに動く。

`init` は本来 `lib/utils.ts`（cn）と CSS のテーマ変数も生成するが、手書きで補った：

- `lib/utils.ts`：`cn` / `WithElementRef` / `WithoutChildren` / `WithoutChildrenOrChild`
- `routes/layout.css`：`@theme inline` ブロック + `:root` / `.dark` の OKLCH テーマ変数

### AuthStore（Svelte 5 runes）

```ts
class AuthStore {
    user = $state<User | null>(null);
    isLoading = $state(true);
    get isAuthenticated(): boolean { return this.user !== null; }

    async init() {
        try { this.user = await api.me(); }
        catch { this.user = null; }
        finally { this.isLoading = false; }
    }

    async login(u, p) { this.user = await api.login(u, p); }
    async logout() {
        await api.logout();
        this.user = null;
        await goto("/login");
    }
}
export const authStore = new AuthStore();
```

`$state` で reactive に持ち、`isAuthenticated` は getter で派生（`$derived` でも可だがクラスでは getter の方が素直）。context API は使わず、シングルトンを export する。

### 認証ガード（+layout.svelte の $effect）

```ts
$effect(() => {
    if (authStore.isLoading) return;
    const path = page.url.pathname;
    if (!authStore.isAuthenticated && path !== "/login") goto("/login");
    else if (authStore.isAuthenticated && path === "/login") goto("/");
});
```

`$effect` は依存（`authStore.user` / `page.url.pathname`）が変わるたび自動で再実行される。`isLoading` 中は何もしない（チラつき防止）。

## 実装

### 主要画面

**/login**

- `Card.Root` の中に `username / password` の `Input` と `Button`
- submit で `authStore.login(...)` → 成功なら `goto('/')`
- 失敗時は赤文字でエラー表示（`text-destructive`）

**/**（校正画面）

- 上部：`Textarea` + 「校正する」ボタン
- ローディング中：`Skeleton`
- エラー時：`Alert.Root variant="destructive"`
- 結果：`Card` に
  - `Badge`（スコア）
  - 修正後の本文（`whitespace-pre-wrap`）
  - 指摘事項リスト（category Badge + span / suggestion / reason）

## 検証

### 自動

| 項目 | 結果 |
|---|---|
| `cd backend && uv run pytest -q` | 14 件 pass（CORS 追加で破綻無し） |
| `cd frontend && bun run check` | 0 errors |
| `cd frontend && bun run build` | 成功（adapter-auto の警告は本番デプロイ時に対処） |

### 手動結合テスト（実 Gemini）

```bash
# .env を準備
echo "GOOGLE_API_KEY=実物のキー" >> backend/.env
echo "INITIAL_ADMIN_PASSWORD=admin1234" >> backend/.env

# DB 起動
cd backend && docker compose -f docker/compose.yml up -d

# backend 起動（:8000）
uv run uvicorn api.main:app --reload

# frontend 起動（:5173、別ターミナル）
cd frontend && bun install && bun run dev
```

ブラウザで `http://localhost:5173` を開き、

1. 未ログインなので自動で `/login` に飛ぶこと
2. `admin / admin1234` でログイン → `/` に遷移
3. 「お疲れさまです、本日の打合せ件…」のような誤字を含む文を貼って **校正する**
4. 結果カードに `corrected` / `score` / `issues` が表示
5. 右上 **ログアウト** で `/login` に戻ること

DevTools Network で確認：

- `POST /api/login` のレスポンスに `Set-Cookie: token=...; HttpOnly`
- `POST /api/correct` のリクエストに `Cookie: token=...`
- `Access-Control-Allow-Origin: http://localhost:5173` / `Access-Control-Allow-Credentials: true`

### 確認観点（architecture.md より）

- [x] 設計通り：SPA、Cookie 認証、永続化なし
- [x] 環境変数をハードコードしてない（`VITE_API_URL` / `ALLOWED_ORIGINS`）
- [x] エラーハンドリング：401 で /login リダイレクト、API エラーは赤い Alert で表示
- [x] LLM 生成内容を理解：shadcn の各コンポーネントの import 経路と props を doc に記載

## 次フェーズへの引き継ぎ

phase 5（管理者機能）で着手するもの：

- `POST /api/admin/user`（ユーザー登録、`Depends(require_admin)`）
- `PATCH /api/admin/user/{id}/deactivate`（無効化）
- `/admin` 画面：ユーザー一覧 table + 登録フォーム
- 一般 user が `/admin` を踏んだ時は 403 → トーストで案内、自動で `/` に戻す

注意点：

- 本番（ドメインが分かれる）ではフロントとバックの origin が cross-site になり、Cookie の `SameSite=Lax` では送られない。`SameSite=None; Secure` への切替が必要。phase 6 課題。
- `adapter-auto` のビルド警告は、最終デプロイ先（Vercel / Netlify / Node）に応じて `adapter-static` 等へ差し替えること。
- `lefthook` の pre-push に frontend の `bun run check` / `bun run lint` を追加するのは phase 5 以降で検討。
