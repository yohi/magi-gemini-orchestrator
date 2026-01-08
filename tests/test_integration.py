import os
import pytest
import asyncio
from dotenv import load_dotenv
from magi_orchestrator import GeminiNativeClient, MagiOrchestrator, OrchestratorSettings
from magi.models import ConsensusResult

load_dotenv()

# APIキーがない場合はスキップ
api_key = os.environ.get("MAGI_GEMINI_API_KEY", "")
requires_api_key = pytest.mark.skipif(not api_key, reason="MAGI_GEMINI_API_KEY not set")


@pytest.mark.asyncio
@requires_api_key
async def test_client_connectivity():
    """Gemini API への基本接続テスト"""
    client = GeminiNativeClient(api_key=api_key)
    try:
        response = await client.generate_content(
            model="gemini-3-flash-preview",
            contents="Hello, are you online?",
            system_instruction="Reply with 'Yes' only.",
        )
        assert len(response) > 0
    finally:
        await client.close()


@pytest.mark.asyncio
@requires_api_key
async def test_orchestrator_consult():
    """MagiOrchestrator の統合テスト"""
    client = GeminiNativeClient(api_key=api_key)
    orchestrator = MagiOrchestrator(client)

    try:
        # シンプルな質問で合議を実行
        result = await orchestrator.consult(
            "Is Python a good programming language for AI?"
        )

        assert isinstance(result, ConsensusResult)
        assert result.final_decision is not None
        assert len(result.thinking_results) == 3  # 3賢者
        assert len(result.debate_results) >= 1  # 議論フェーズがあること
        assert len(result.voting_results) == 3  # 3票

        # 思考内容の確認
        for persona, thinking in result.thinking_results.items():
            assert thinking.content
            assert len(thinking.content) > 10
            assert "[ERROR]" not in thinking.content, (
                f"API Error in thinking: {thinking.content}"
            )

        # 議論内容の確認
        debate_round = result.debate_results[0]
        assert debate_round.round_number == 1
        assert len(debate_round.outputs) == 3

    finally:
        await client.close()
