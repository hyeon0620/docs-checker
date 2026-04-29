"""エンドポイントの入出力スキーマ（Pydantic モデル）。"""

from pydantic import BaseModel

# === 認証 ===


class LoginIn(BaseModel):
    """POST /api/login のリクエストボディ。"""

    username: str
    password: str


class UserOut(BaseModel):
    """ユーザー情報のレスポンス。Cookie はヘッダ側で別途返すため含めない。"""

    id: int
    username: str
    role: str


# === 校正 ===


class IssueItem(BaseModel):
    """校正での指摘1件。Gemini が構造化出力で返す。"""

    category: str  # "typo" | "keigo" | "expression"
    span: str  # 原文の該当部分
    suggestion: str  # 修正案
    reason: str  # 修正理由


class CorrectIn(BaseModel):
    """POST /api/correct のリクエストボディ。"""

    original: str


class CorrectOut(BaseModel):
    """校正結果。corrected は LLM が返す修正後テキスト。永続化はしない。"""

    corrected: str
    score: int  # 0-100
    issues: list[IssueItem]
