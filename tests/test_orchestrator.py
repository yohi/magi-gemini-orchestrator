"""MagiOrchestrator のユニットテスト"""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from magi.models import Decision, PersonaType, Vote


class TestVoteParsing:
    """投票結果パースのテスト"""

    def test_parse_approve_vote(self):
        """APPROVE 投票のパース"""
        from magi_orchestrator.orchestrator import MagiOrchestrator

        mock_client = MagicMock()
        orchestrator = MagiOrchestrator(mock_client)

        raw = """VOTE: APPROVE
REASON: この設計は論理的に正しく、実装可能です。"""

        result = orchestrator._parse_vote_output(PersonaType.MELCHIOR, raw)

        assert result.vote == Vote.APPROVE
        assert "論理的に正しく" in result.reason

    def test_parse_deny_vote(self):
        """DENY 投票のパース"""
        from magi_orchestrator.orchestrator import MagiOrchestrator

        mock_client = MagicMock()
        orchestrator = MagiOrchestrator(mock_client)

        raw = """VOTE: DENY
REASON: セキュリティリスクが高すぎます。"""

        result = orchestrator._parse_vote_output(PersonaType.BALTHASAR, raw)

        assert result.vote == Vote.DENY
        assert "セキュリティリスク" in result.reason

    def test_parse_conditional_vote_with_conditions(self):
        """CONDITIONAL 投票のパース（条件付き）"""
        from magi_orchestrator.orchestrator import MagiOrchestrator

        mock_client = MagicMock()
        orchestrator = MagiOrchestrator(mock_client)

        raw = """VOTE: CONDITIONAL
REASON: いくつかの改善が必要です。
CONDITIONS: テストカバレッジ80%以上, コードレビュー必須, 段階的デプロイ"""

        result = orchestrator._parse_vote_output(PersonaType.CASPER, raw)

        assert result.vote == Vote.CONDITIONAL
        assert result.conditions is not None
        assert len(result.conditions) == 3
        assert "テストカバレッジ80%以上" in result.conditions

    def test_parse_fallback_to_conditional(self):
        """不明な投票形式は CONDITIONAL にフォールバック"""
        from magi_orchestrator.orchestrator import MagiOrchestrator

        mock_client = MagicMock()
        orchestrator = MagiOrchestrator(mock_client)

        raw = """この設計は興味深いですが、判断が難しいです。"""

        result = orchestrator._parse_vote_output(PersonaType.MELCHIOR, raw)

        assert result.vote == Vote.CONDITIONAL


class TestVotingTally:
    """投票集計のテスト"""

    def test_majority_approve(self):
        """過半数が APPROVE の場合"""
        from magi.models import VotingTally

        tally = VotingTally(approve_count=2, deny_count=1, conditional_count=0)
        decision = tally.get_decision("majority")

        assert decision == Decision.APPROVED

    def test_majority_deny(self):
        """過半数が DENY の場合"""
        from magi.models import VotingTally

        tally = VotingTally(approve_count=0, deny_count=2, conditional_count=1)
        decision = tally.get_decision("majority")

        assert decision == Decision.DENIED

    def test_majority_conditional(self):
        """過半数がない場合は CONDITIONAL"""
        from magi.models import VotingTally

        tally = VotingTally(approve_count=1, deny_count=1, conditional_count=1)
        decision = tally.get_decision("majority")

        assert decision == Decision.CONDITIONAL

    def test_unanimous_approve(self):
        """全員が APPROVE の場合"""
        from magi.models import VotingTally

        tally = VotingTally(approve_count=3, deny_count=0, conditional_count=0)
        decision = tally.get_decision("unanimous")

        assert decision == Decision.APPROVED

    def test_unanimous_with_one_deny(self):
        """1人でも DENY がいれば DENIED"""
        from magi.models import VotingTally

        tally = VotingTally(approve_count=2, deny_count=1, conditional_count=0)
        decision = tally.get_decision("unanimous")

        assert decision == Decision.DENIED


class TestAgentConfigs:
    """エージェント設定のテスト"""

    def test_melchior_config(self):
        """MELCHIOR 設定の確認"""
        from magi_orchestrator.agents import MELCHIOR_CONFIG

        assert MELCHIOR_CONFIG.persona_type == PersonaType.MELCHIOR
        assert MELCHIOR_CONFIG.model == "gemini-3-flash-preview"
        assert MELCHIOR_CONFIG.temperature == 0.2

    def test_balthasar_config(self):
        """BALTHASAR 設定の確認"""
        from magi_orchestrator.agents import BALTHASAR_CONFIG

        assert BALTHASAR_CONFIG.persona_type == PersonaType.BALTHASAR
        assert BALTHASAR_CONFIG.model == "gemini-3-flash-preview"
        assert BALTHASAR_CONFIG.temperature == 0.5

    def test_casper_config(self):
        """CASPER 設定の確認"""
        from magi_orchestrator.agents import CASPER_CONFIG

        assert CASPER_CONFIG.persona_type == PersonaType.CASPER
        assert CASPER_CONFIG.model == "gemini-3-flash-preview"
        assert CASPER_CONFIG.temperature == 0.8

    def test_all_agents_list(self):
        """ALL_AGENTS リストの確認"""
        from magi_orchestrator.agents import ALL_AGENTS

        assert len(ALL_AGENTS) == 3
        persona_types = {a.persona_type for a in ALL_AGENTS}
        assert PersonaType.MELCHIOR in persona_types
        assert PersonaType.BALTHASAR in persona_types
        assert PersonaType.CASPER in persona_types


class TestOrchestratorSettings:
    """設定のテスト"""

    def test_default_settings(self):
        """デフォルト設定の確認"""
        with patch.dict("os.environ", {"MAGI_GEMINI_API_KEY": "test-key"}):
            from magi_orchestrator.config import OrchestratorSettings

            settings = OrchestratorSettings()

            assert settings.api_key == "test-key"
            assert settings.default_model == "gemini-3-flash-preview"
            assert settings.voting_threshold == "majority"
            assert settings.timeout == 60

    def test_dump_masked(self):
        """機微情報マスクの確認"""
        with patch.dict("os.environ", {"MAGI_GEMINI_API_KEY": "sk-1234567890abcdef"}):
            from magi_orchestrator.config import OrchestratorSettings

            settings = OrchestratorSettings()
            masked = settings.dump_masked()

            assert "1234567890" not in masked["api_key"]
            assert "..." in masked["api_key"]


@pytest.mark.asyncio
class TestGeminiNativeClient:
    """GeminiNativeClient のテスト"""

    async def test_generate_concurrent_with_multimodal_content(self):
        """マルチモーダル入力のモックテスト"""
        from google.genai import types
        from magi_orchestrator.client import GeminiNativeClient

        with patch("magi_orchestrator.client.genai") as mock_genai:
            mock_response = MagicMock()
            mock_response.text = "Analysis result"

            mock_aclient = AsyncMock()
            mock_aclient.models.generate_content = AsyncMock(return_value=mock_response)

            mock_client_instance = MagicMock()
            mock_client_instance.aio = mock_aclient
            mock_genai.Client.return_value = mock_client_instance

            client = GeminiNativeClient(api_key="test-key")

            # Part オブジェクトを含むリクエスト
            part = types.Part.from_bytes(data=b"dummy", mime_type="image/png")
            requests = [
                {
                    "model": "gemini-1.5-flash",
                    "contents": ["Explain this image", part],
                    "config": {},
                }
            ]

            results = await client.generate_concurrent(requests)

            assert len(results) == 1
            assert results[0] == "Analysis result"

            # 呼び出し引数の検証
            call_args = mock_aclient.models.generate_content.call_args
            assert call_args is not None
            _, kwargs = call_args
            assert len(kwargs["contents"]) == 2
            assert kwargs["contents"][1] == part


@pytest.mark.asyncio
class TestOrchestrator:
    """MagiOrchestrator のテスト"""

    async def test_thinking_phase_with_attachments(self):
        """Thinking Phase での添付ファイル処理テスト"""
        from magi.models import Attachment
        from magi_orchestrator.orchestrator import MagiOrchestrator

        mock_client = MagicMock()
        mock_client.generate_concurrent = AsyncMock(
            return_value=["Analysis 1", "Analysis 2", "Analysis 3"]
        )

        orchestrator = MagiOrchestrator(mock_client)

        attachments = [
            Attachment(
                mime_type="image/png", data=b"fake_image_data", filename="test.png"
            )
        ]

        await orchestrator._run_thinking_phase("Analyze this", attachments)

        # generate_concurrent が呼ばれたことを確認
        assert mock_client.generate_concurrent.called
        call_args = mock_client.generate_concurrent.call_args
        assert call_args is not None
        requests = call_args[0][0]

        # 各リクエストの contents に Part が含まれているか確認
        for req in requests:
            contents = req["contents"]
            # プロンプト(str) + Part のはず
            assert len(contents) == 2
            assert isinstance(contents[0], str)
            # google.genai.types.Part の検証は難しい（モックでないため）が、
            # 少なくともオブジェクトが存在することを確認
            part = contents[1]
            assert hasattr(part, "inline_data")
            assert part.inline_data.mime_type == "image/png"
            assert part.inline_data.data == b"fake_image_data"
