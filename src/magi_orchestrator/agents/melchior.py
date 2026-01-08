"""MELCHIOR-1 エージェント設定

論理・科学担当。決定論的な分析を行う。
Temperature: 0.2（低い = 決定論的）
"""

from magi.models import PersonaType
from magi.agents.persona import MELCHIOR_BASE_PROMPT

from magi_orchestrator.agents.base import AgentConfig


MELCHIOR_CONFIG = AgentConfig(
    persona_type=PersonaType.MELCHIOR,
    model="gemini-2.0-flash",
    temperature=0.2,
    system_instruction=MELCHIOR_BASE_PROMPT,
)
