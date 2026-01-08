"""エージェント基底クラス

AgentConfig: エージェントの設定を保持するデータクラス。
"""

from dataclasses import dataclass
from typing import Optional

from magi.models import PersonaType


@dataclass
class AgentConfig:
    """エージェント設定

    Attributes:
        persona_type: ペルソナタイプ（MELCHIOR / BALTHASAR / CASPER）
        model: 使用するモデル名（例: "gemini-1.5-flash"）
        temperature: 温度パラメータ（0.0〜1.0）
        system_instruction: システム命令（ペルソナ定義）
        cached_content: コンテキストキャッシュ名（オプション）
    """

    persona_type: PersonaType
    model: str
    temperature: float
    system_instruction: str
    cached_content: Optional[str] = None

    @property
    def name(self) -> str:
        """ペルソナ名を返す（例: "MELCHIOR"）"""
        return self.persona_type.value.upper()
