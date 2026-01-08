"""エージェントモジュール

MAGI 3賢者のエージェント設定を提供する。
"""

from magi_orchestrator.agents.base import AgentConfig
from magi_orchestrator.agents.melchior import MELCHIOR_CONFIG
from magi_orchestrator.agents.balthasar import BALTHASAR_CONFIG
from magi_orchestrator.agents.casper import CASPER_CONFIG

__all__ = [
    "AgentConfig",
    "MELCHIOR_CONFIG",
    "BALTHASAR_CONFIG",
    "CASPER_CONFIG",
]

# 全エージェント設定のリスト
ALL_AGENTS = [MELCHIOR_CONFIG, BALTHASAR_CONFIG, CASPER_CONFIG]
