"""MagiOrchestrator

google-genai SDK ネイティブの MAGI オーケストレーター。
3賢者（MELCHIOR, BALTHASAR, CASPER）による合議プロセスを実行する。

フェーズ:
    1. Thinking Phase: 3エージェントが並列で独立思考
    2. Voting Phase: 3エージェントが並列で投票
    3. Decision: 投票結果を集計して最終判定
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, List, Optional

from magi.models import (
    ConsensusResult,
    Decision,
    PersonaType,
    ThinkingOutput,
    Vote,
    VoteOutput,
    VotingTally,
)

from magi_orchestrator.agents import ALL_AGENTS, AgentConfig
from magi_orchestrator.cache import CacheManager
from magi_orchestrator.client import GeminiNativeClient


class MagiOrchestrator:
    """MAGI 3賢者オーケストレーター

    google-genai SDK を使用して3つのエージェントを並列実行し、
    合議プロセスを通じて最終判定を導き出す。

    Example:
        >>> from magi_orchestrator import GeminiNativeClient, MagiOrchestrator
        >>> client = GeminiNativeClient(api_key="your-api-key")
        >>> orchestrator = MagiOrchestrator(client)
        >>> result = await orchestrator.consult("この設計は適切ですか？")
        >>> print(result.final_decision)
    """

    def __init__(
        self,
        client: GeminiNativeClient,
        cache_manager: Optional[CacheManager] = None,
        voting_threshold: str = "majority",
        agents: Optional[List[AgentConfig]] = None,
    ) -> None:
        """オーケストレーターを初期化

        Args:
            client: GeminiNativeClient インスタンス
            cache_manager: CacheManager インスタンス（オプション）
            voting_threshold: 投票閾値（"majority" または "unanimous"）
            agents: エージェント設定リスト（デフォルトは3賢者）
        """
        self.client = client
        self.cache_manager = cache_manager
        self.voting_threshold = voting_threshold
        self.agents = agents or ALL_AGENTS

    async def consult(self, query: str) -> ConsensusResult:
        """3賢者への問い合わせを実行

        Args:
            query: ユーザーからの質問/議題

        Returns:
            ConsensusResult: 合議プロセスの結果
        """
        # Phase 1: Thinking（並列実行）
        thinking_results = await self._run_thinking_phase(query)

        # Phase 2: Voting（並列実行）
        voting_results = await self._run_voting_phase(query, thinking_results)

        # Phase 3: Decision
        tally = self._tally_votes(voting_results)
        decision = tally.get_decision(self.voting_threshold)
        exit_code = self._get_exit_code(decision)

        # 条件を収集
        all_conditions = self._collect_conditions(voting_results)

        return ConsensusResult(
            thinking_results={pt.value: to for pt, to in thinking_results.items()},
            debate_results=[],  # 簡略版では Debate Phase を省略
            voting_results=voting_results,
            final_decision=decision,
            exit_code=exit_code,
            all_conditions=all_conditions if all_conditions else None,
        )

    async def _run_thinking_phase(
        self,
        query: str,
    ) -> Dict[PersonaType, ThinkingOutput]:
        """Thinking Phase: 3エージェント並列実行

        各エージェントが独立して思考を生成する。

        Args:
            query: ユーザーからの質問

        Returns:
            ペルソナタイプごとの思考結果
        """
        thinking_prompt = f"""以下の議題について、あなたの立場から分析してください。

【議題】
{query}

【分析の観点】
- あなたの役割に基づいた視点からの評価
- 潜在的なリスクと機会の特定
- 推奨されるアクション

明確で構造化された分析を提供してください。"""

        requests = [
            {
                "model": agent.model,
                "contents": thinking_prompt,
                "config": {
                    "system_instruction": agent.system_instruction,
                    "temperature": agent.temperature,
                    "cached_content": self._get_cache_name(agent),
                },
            }
            for agent in self.agents
        ]

        results = await self.client.generate_concurrent(requests)
        now = datetime.now()

        return {
            agent.persona_type: ThinkingOutput(
                persona_type=agent.persona_type,
                content=result,
                timestamp=now,
            )
            for agent, result in zip(self.agents, results)
        }

    async def _run_voting_phase(
        self,
        query: str,
        thinking_results: Dict[PersonaType, ThinkingOutput],
    ) -> Dict[PersonaType, VoteOutput]:
        """Voting Phase: 投票を並列実行

        各エージェントが全員の分析を参照して投票する。

        Args:
            query: 元の質問
            thinking_results: Thinking Phase の結果

        Returns:
            ペルソナタイプごとの投票結果
        """
        # 他エージェントの思考をコンテキストとして構築
        context_parts = []
        for pt, to in thinking_results.items():
            context_parts.append(f"【{pt.value.upper()}の分析】\n{to.content}")
        context = "\n\n".join(context_parts)

        vote_prompt = f"""以下の分析結果を踏まえ、元の議題に対して投票してください。

【元の議題】
{query}

【各エージェントの分析】
{context}

【投票形式】
以下の形式で厳密に回答してください：

VOTE: [APPROVE または DENY または CONDITIONAL]
REASON: [投票理由を1-2文で簡潔に]
CONDITIONS: [CONDITIONAL の場合のみ、条件をカンマ区切りで記載]

注意: VOTE は必ず APPROVE, DENY, CONDITIONAL のいずれか1つを選択してください。"""

        requests = [
            {
                "model": agent.model,
                "contents": vote_prompt,
                "config": {
                    "system_instruction": agent.system_instruction,
                    "temperature": 0.3,  # 投票時は低温度で安定した出力
                },
            }
            for agent in self.agents
        ]

        results = await self.client.generate_concurrent(requests)

        return {
            agent.persona_type: self._parse_vote_output(agent.persona_type, result)
            for agent, result in zip(self.agents, results)
        }

    def _parse_vote_output(
        self,
        persona_type: PersonaType,
        raw: str,
    ) -> VoteOutput:
        """投票結果をパース

        Args:
            persona_type: ペルソナタイプ
            raw: 生のレスポンステキスト

        Returns:
            パースされた VoteOutput
        """
        # デフォルト値
        vote = Vote.CONDITIONAL
        reason = raw
        conditions: Optional[List[str]] = None

        # VOTE をパース
        vote_match = re.search(
            r"VOTE:\s*(APPROVE|DENY|CONDITIONAL)", raw, re.IGNORECASE
        )
        if vote_match:
            vote_str = vote_match.group(1).upper()
            if vote_str == "APPROVE":
                vote = Vote.APPROVE
            elif vote_str == "DENY":
                vote = Vote.DENY
            else:
                vote = Vote.CONDITIONAL

        # REASON をパース
        reason_match = re.search(r"REASON:\s*(.+?)(?=CONDITIONS:|$)", raw, re.DOTALL)
        if reason_match:
            reason = reason_match.group(1).strip()

        # CONDITIONS をパース（CONDITIONAL の場合）
        if vote == Vote.CONDITIONAL:
            cond_match = re.search(r"CONDITIONS:\s*(.+?)$", raw, re.DOTALL)
            if cond_match:
                cond_text = cond_match.group(1).strip()
                conditions = [c.strip() for c in cond_text.split(",") if c.strip()]

        return VoteOutput(
            persona_type=persona_type,
            vote=vote,
            reason=reason,
            conditions=conditions,
        )

    def _tally_votes(
        self,
        voting_results: Dict[PersonaType, VoteOutput],
    ) -> VotingTally:
        """投票結果を集計

        Args:
            voting_results: 投票結果

        Returns:
            VotingTally: 集計結果
        """
        approve_count = sum(
            1 for v in voting_results.values() if v.vote == Vote.APPROVE
        )
        deny_count = sum(1 for v in voting_results.values() if v.vote == Vote.DENY)
        conditional_count = sum(
            1 for v in voting_results.values() if v.vote == Vote.CONDITIONAL
        )

        return VotingTally(
            approve_count=approve_count,
            deny_count=deny_count,
            conditional_count=conditional_count,
        )

    def _get_exit_code(self, decision: Decision) -> int:
        """最終判定に対応する終了コードを取得

        Args:
            decision: 最終判定

        Returns:
            終了コード（0=APPROVED, 1=DENIED, 2=CONDITIONAL）
        """
        if decision == Decision.APPROVED:
            return 0
        elif decision == Decision.DENIED:
            return 1
        else:
            return 2

    def _collect_conditions(
        self,
        voting_results: Dict[PersonaType, VoteOutput],
    ) -> List[str]:
        """全投票から条件を収集

        Args:
            voting_results: 投票結果

        Returns:
            条件のリスト
        """
        conditions: List[str] = []
        for vo in voting_results.values():
            if vo.conditions:
                conditions.extend(vo.conditions)
        return conditions

    def _get_cache_name(self, agent: AgentConfig) -> Optional[str]:
        """エージェントのキャッシュ名を取得

        Args:
            agent: エージェント設定

        Returns:
            キャッシュ名（存在しない場合は None）
        """
        if agent.cached_content:
            return agent.cached_content
        if self.cache_manager:
            return self.cache_manager.get_cache_name(agent.persona_type.value)
        return None
