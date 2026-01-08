"""MAGI Gemini Orchestrator

google-genai SDK ネイティブの MAGI システム実装。
3賢者（MELCHIOR, BALTHASAR, CASPER）による合議プロセスを提供する。
"""

from magi_orchestrator.config import OrchestratorSettings
from magi_orchestrator.client import GeminiNativeClient
from magi_orchestrator.orchestrator import MagiOrchestrator
from magi_orchestrator.cache import CacheManager

__version__ = "0.1.0"
__all__ = [
    "OrchestratorSettings",
    "GeminiNativeClient",
    "MagiOrchestrator",
    "CacheManager",
]


def main() -> None:
    """CLI エントリーポイント（将来実装予定）"""
    print(f"MAGI Gemini Orchestrator v{__version__}")
    print("Use MagiOrchestrator class for programmatic access.")
