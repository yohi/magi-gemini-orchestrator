"""CacheManager

コンテキストキャッシュを管理する。
ペルソナ定義（システム命令）をキャッシュして、
推論コストとレイテンシを削減する。
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import logging

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class CacheManager:
    """ペルソナ定義のコンテキストキャッシュを管理

    Gemini API のコンテキストキャッシュ機能を使用して、
    長大なシステム命令をキャッシュし、APIコストを削減する。

    Example:
        >>> from google import genai
        >>> client = genai.Client(api_key="your-api-key")
        >>> cache_manager = CacheManager(client)
        >>> cache_name = await cache_manager.create_persona_cache(
        ...     persona_name="melchior",
        ...     model="gemini-1.5-flash",
        ...     system_instruction="You are MELCHIOR-1...",
        ... )
        >>> print(cache_name)
        caches/12345
    """

    def __init__(self, client: genai.Client) -> None:
        """CacheManager を初期化

        Args:
            client: google.genai.Client インスタンス
        """
        self._client = client
        self._caches: Dict[str, str] = {}  # persona_name -> cache_name

    def create_persona_cache(
        self,
        persona_name: str,
        model: str,
        system_instruction: str,
        ttl_seconds: int = 3600,
    ) -> str:
        """ペルソナのシステム命令をキャッシュ

        Args:
            persona_name: ペルソナ名（例: "melchior"）
            model: モデル名（例: "gemini-1.5-flash"）
            system_instruction: システム命令
            ttl_seconds: キャッシュの有効期限（秒）

        Returns:
            キャッシュ名（例: "caches/12345"）
        """
        cache = self._client.caches.create(
            model=model,
            config=types.CreateCachedContentConfig(
                system_instruction=system_instruction,
                display_name=f"magi-{persona_name}",
                ttl=f"{ttl_seconds}s",
            ),
        )
        cache_name = cache.name
        self._caches[persona_name] = cache_name
        return cache_name

    def get_cache_name(self, persona_name: str) -> Optional[str]:
        """キャッシュ名を取得

        Args:
            persona_name: ペルソナ名

        Returns:
            キャッシュ名（存在しない場合は None）
        """
        return self._caches.get(persona_name)

    def list_caches(self) -> Dict[str, str]:
        """全キャッシュを取得

        Returns:
            ペルソナ名 -> キャッシュ名 のマッピング
        """
        return dict(self._caches)

    def clear_cache(self, persona_name: str) -> bool:
        """キャッシュを削除

        Args:
            persona_name: ペルソナ名

        Returns:
            削除に成功した場合 True
        """
        if persona_name in self._caches:
            cache_name = self._caches.pop(persona_name)
            try:
                self._client.caches.delete(name=cache_name)
                return True
            except Exception as e:
                logger.error(
                    f"Failed to delete cache for {persona_name} ({cache_name}): {e}"
                )
                return False
        return False

    def warmup_all_personas(
        self,
        model: str = "gemini-1.5-flash",
        ttl_seconds: int = 3600,
    ) -> Dict[str, str]:
        """全ペルソナのキャッシュを事前作成

        Args:
            model: 使用するモデル名
            ttl_seconds: キャッシュの有効期限（秒）

        Returns:
            ペルソナ名 -> キャッシュ名 のマッピング
        """
        from magi_orchestrator.agents import ALL_AGENTS

        for config in ALL_AGENTS:
            self.create_persona_cache(
                persona_name=config.persona_type.value,
                model=model,
                system_instruction=config.system_instruction,
                ttl_seconds=ttl_seconds,
            )

        return dict(self._caches)


class NullCacheManager:
    """キャッシュを使用しないダミー実装

    テストやキャッシュ不要な場合に使用する。
    """

    def create_persona_cache(self, *args: Any, **kwargs: Any) -> str:
        return ""

    def get_cache_name(self, persona_name: str) -> Optional[str]:
        return None

    def list_caches(self) -> Dict[str, str]:
        return {}

    def clear_cache(self, persona_name: str) -> bool:
        return False

    def warmup_all_personas(self, *args: Any, **kwargs: Any) -> Dict[str, str]:
        return {}
