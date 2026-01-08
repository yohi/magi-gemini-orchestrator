"""Pydantic 設定モジュール

OrchestratorSettings: MAGI Gemini Orchestrator の設定を管理する。
環境変数または .env ファイルから設定を読み込む。
"""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OrchestratorSettings(BaseSettings):
    """MAGI Gemini Orchestrator 設定

    環境変数プレフィックス: MAGI_GEMINI_

    Attributes:
        api_key: Gemini API Key（必須）
        default_model: デフォルトモデル
        voting_threshold: 投票閾値（majority / unanimous）
        cache_ttl_seconds: コンテキストキャッシュ TTL（秒）
        timeout: API タイムアウト（秒）
        max_output_tokens: 最大出力トークン数
    """

    model_config = SettingsConfigDict(
        env_prefix="MAGI_GEMINI_",
        env_file=".env",
        extra="ignore",
    )

    # API 設定
    api_key: str = Field(..., description="Gemini API Key")
    default_model: str = Field(
        default="gemini-1.5-flash",
        description="デフォルトモデル",
    )
    timeout: int = Field(default=60, ge=1, description="API タイムアウト（秒）")

    # 合議設定
    voting_threshold: Literal["majority", "unanimous"] = Field(
        default="majority",
        description="投票閾値",
    )

    # キャッシュ設定
    cache_ttl_seconds: int = Field(
        default=3600,
        ge=60,
        description="コンテキストキャッシュ TTL（秒）",
    )

    # 生成設定
    max_output_tokens: int = Field(
        default=4096,
        ge=1,
        le=8192,
        description="最大出力トークン数",
    )

    def dump_masked(self) -> dict:
        """機微情報をマスクした設定を返却する"""
        data = self.model_dump()
        api_key = data.get("api_key")
        if api_key:
            data["api_key"] = (
                f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
            )
        return data
