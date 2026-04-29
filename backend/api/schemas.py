"""エンドポイントの入出力スキーマ（Pydantic モデル）。"""

from pydantic import BaseModel


class LoginIn(BaseModel):
    """POST /api/login のリクエストボディ。"""

    username: str
    password: str


class UserOut(BaseModel):
    """ユーザー情報のレスポンス。Cookie はヘッダ側で別途返すため含めない。"""

    id: int
    username: str
    role: str
