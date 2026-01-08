"""BALTHASAR-2 エージェント設定

倫理・保護担当。バランスの取れた分析を行う。
Temperature: 0.5（中間 = バランス）
"""

from magi.models import PersonaType
from magi.agents.persona import BALTHASAR_BASE_PROMPT

from magi_orchestrator.agents.base import AgentConfig


BALTHASAR_CONFIG = AgentConfig(
    persona_type=PersonaType.BALTHASAR,
    model="gemini-3-flash-preview",
    temperature=0.5,
    system_instruction=BALTHASAR_BASE_PROMPT,
)
