"""CASPER-3 エージェント設定

欲望・実利担当。創造的な分析を行う。
Temperature: 0.8（高い = 創造的）
"""

from magi.models import PersonaType
from magi.agents.persona import CASPER_BASE_PROMPT

from magi_orchestrator.agents.base import AgentConfig


CASPER_CONFIG = AgentConfig(
    persona_type=PersonaType.CASPER,
    model="gemini-2.0-flash",
    temperature=0.8,
    system_instruction=CASPER_BASE_PROMPT,
)
