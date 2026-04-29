# CLAUDE.md

このリポジトリでコード生成・編集を行うときの方針。

## コードの並び順（read order）

ファイルを上から読んだ時に**話が追える**順序にする。Python の慣習（helpers 先 → caller 後のボトムアップ）よりも、読み手の理解を優先する。

### ルール

1. **トップダウン**：主役（外部から呼ばれる関数 / API）を上に置き、その内部で使うヘルパーを直下に置く
2. **機能でグループ化**：関連する関数同士を近くにまとめ、セクション見出しコメントで区切る（例：`# === ログイン処理 ===`）
3. **「ヘルパー先・主役後」を避ける**：先に小さい部品が並んで、ずっと下の方で組み立てる構造は禁止（読んでいる時に「これは何のため？」が解消されない）

### 例（auth.py の構造）

```python
# === ユーザー登録 ===
def hash_password(...)               # 主役

# === ログイン処理 ===
async def authenticate(...)          # 主役：/api/login が呼ぶ
def verify_password(...)             # ↑authenticate 内で使う
def create_token(...)                # 主役：ログイン成功時に JWT 発行

# === リクエストごとの認証 ===
async def current_user(...)          # 主役：保護エンドポイントの依存
def decode_token(...)                # ↑current_user 内で使う
async def require_admin(...)         # 主役：admin 限定エンドポイントの依存
```

### docstring の形式

各関数の docstring は **「〇〇時：何をする」** の1行で書く。
他の関数内で呼ばれる内部ヘルパーの場合は、**呼び出し元の関数名を `〇〇時` に含める**。

良い例：

- `"ユーザー登録時：平文パスワードを bcrypt ハッシュに変換する。"`
- `"ログイン時（authenticate 内）：入力された平文と DB のハッシュを照合する。"`

```
def verify_password(password: str, password_hash: str) -> bool:
    """ログイン時（authenticate 内）：入力された平文と DB のハッシュを照合する。"""
    return bcrypt.checkpw(password.encode(), password_hash.encode())
```

悪い例（用途が分からない）：

- `"パスワードをハッシュ化する。"`

## ファイル分割の方針

### Pydantic スキーマ（リクエスト/レスポンス）

- **3個までは `main.py` 内に置く**（同居）
- **4個以上になったら `schemas.py` に切り出す**
- main.py がエンドポイント本体だけになるよう、肥大化したらすぐ分離する

### 該当する基準

スキーマだけでなく、**何かが3個以上になりそう**なら独立ファイルを検討：

- 設定値が増える → `config.py`
- DB操作が増える → `db.py`
- 認証ロジックが複雑化 → `auth.py`
- 起動時タスクが複数 → `initial_admin.py` のように責務ごとのファイル

→ ptw-respec のように `app/schemas/`, `app/services/` 等のサブディレクトリに分けるのは更にスケールした時。今は1ファイル単位で分離する。

## その他

- 不要なコメントは書かない（自明な what は書かない、why が非自明な時だけ書く）
- 関数の docstring は上記形式の **1行** を基本とし、長い説明が必要な時は本文を追加する
