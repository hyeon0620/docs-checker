"""Gemini 校正の本体。LangChain 経由で構造化出力を得る。"""

from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any

import yaml
from langchain_google_genai import ChatGoogleGenerativeAI

from api.config import settings
from api.schemas import CorrectOut

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "correct.yaml"
_PROMPTS = yaml.safe_load(_PROMPT_PATH.read_text())

_chain: Any = None


# === LLM チェーンの組み立て ===


def _build_chain() -> Any:
    """初回呼び出し時（correct_text 内）：Gemini クライアント + 構造化出力パイプを作る。"""
    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key or None,
    )
    return llm.with_structured_output(CorrectOut)


# === 校正本体 ===


async def correct_text(original: str) -> CorrectOut:
    """校正リクエスト時（main.py の /api/correct から呼ばれる）：
    Gemini に投げて CorrectOut を返す。チェーンは初回のみ構築（遅延初期化）。"""
    global _chain
    if _chain is None:
        _chain = _build_chain()
    messages = [
        {"role": "system", "content": _PROMPTS["system"]},
        {"role": "user", "content": _PROMPTS["user"].format(original=original)},
    ]
    return await _chain.ainvoke(messages)


# === 依存関数 ===


Corrector = Callable[[str], Coroutine[Any, Any, CorrectOut]]


def get_corrector() -> Corrector:
    """FastAPI 依存関数：テストで dependency_overrides によりフェイクに差し替え可能にする。"""
    return correct_text
