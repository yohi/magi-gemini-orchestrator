"""GeminiNativeClient

google-genai SDK を使った非同期クライアント。
複数リクエストの並列実行をサポートする。
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from google import genai
from google.genai import types


class GeminiNativeClient:
    """google-genai SDK ネイティブクライアント

    非同期 API を使用してコンテンツ生成を行う。
    asyncio.gather による並列実行をサポート。

    Example:
        >>> client = GeminiNativeClient(api_key="your-api-key")
        >>> response = await client.generate_content(
        ...     model="gemini-1.5-flash",
        ...     contents="Hello, MAGI!",
        ...     system_instruction="You are a helpful assistant.",
        ... )
        >>> print(response)
    """

    def __init__(self, api_key: str, timeout: int = 60) -> None:
        """クライアントを初期化

        Args:
            api_key: Gemini API Key
            timeout: リクエストタイムアウト（秒）
        """
        self._api_key = api_key
        self._timeout = timeout
        self._client = genai.Client(api_key=api_key)

    async def generate_content(
        self,
        model: str,
        contents: str,
        system_instruction: str,
        temperature: float = 0.7,
        max_output_tokens: int = 4096,
        cached_content: Optional[str] = None,
    ) -> str:
        """非同期コンテンツ生成

        Args:
            model: モデル名（例: "gemini-1.5-flash"）
            contents: ユーザープロンプト
            system_instruction: システム命令
            temperature: 温度パラメータ（0.0〜1.0）
            max_output_tokens: 最大出力トークン数
            cached_content: キャッシュ名（オプション）

        Returns:
            生成されたテキスト
        """
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            cached_content=cached_content,
        )

        async with self._client.aio as aclient:
            response = await aclient.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
            return response.text or ""

    async def generate_concurrent(
        self,
        requests: list[dict[str, Any]],
    ) -> list[str]:
        """複数リクエストを並列実行

        Args:
            requests: リクエストのリスト。各リクエストは以下のキーを持つ:
                - model: モデル名
                - contents: ユーザープロンプト
                - config: GenerateContentConfig の引数（dict）

        Returns:
            生成されたテキストのリスト（リクエスト順）

        Example:
            >>> requests = [
            ...     {"model": "gemini-1.5-flash", "contents": "Q1", "config": {...}},
            ...     {"model": "gemini-1.5-flash", "contents": "Q2", "config": {...}},
            ...     {"model": "gemini-1.5-flash", "contents": "Q3", "config": {...}},
            ... ]
            >>> results = await client.generate_concurrent(requests)
        """
        async with self._client.aio as aclient:
            tasks = [
                aclient.models.generate_content(
                    model=req["model"],
                    contents=req["contents"],
                    config=types.GenerateContentConfig(**req.get("config", {})),
                )
                for req in requests
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 例外をエラーメッセージに変換
            texts: list[str] = []
            for result in results:
                if isinstance(result, Exception):
                    texts.append(f"[ERROR] {type(result).__name__}: {result}")
                else:
                    texts.append(result.text or "")
            return texts

    async def close(self) -> None:
        """クライアントリソースをクリーンアップ"""
        # google-genai SDK は明示的なクローズが不要だが、
        # 将来の拡張のためにインターフェースを用意
        pass

    async def __aenter__(self) -> "GeminiNativeClient":
        return self

    async def __aexit__(self, *_exc: Any) -> None:
        await self.close()
