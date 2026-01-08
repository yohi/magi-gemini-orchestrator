import argparse
import asyncio
import os
import sys
from typing import Optional

from dotenv import load_dotenv

from magi_orchestrator.client import GeminiNativeClient
from magi_orchestrator.config import OrchestratorSettings
from magi_orchestrator.orchestrator import MagiOrchestrator


async def run_magi(query: str, verbose: bool = False) -> None:
    """MAGI システムを実行する"""
    # 設定読み込み
    load_dotenv()
    settings = OrchestratorSettings()

    if not settings.api_key:
        print("Error: MAGI_GEMINI_API_KEY is not set.", file=sys.stderr)
        sys.exit(1)

    if verbose:
        print(f"Model: {settings.default_model}")
        print(f"Threshold: {settings.voting_threshold}")
        print("-" * 50)

    # クライアントとオーケストレーターの初期化
    client = GeminiNativeClient(
        api_key=settings.api_key,
        timeout=settings.timeout,
    )

    try:
        orchestrator = MagiOrchestrator(
            client=client,
            voting_threshold=settings.voting_threshold,
        )

        print(f"MAGI System Processing: '{query}'...\n")

        # 合議実行
        result = await orchestrator.consult(query)

        # 結果表示
        print("=" * 60)
        print(f"FINAL DECISION: {result.final_decision.value.upper()}")
        print("=" * 60)

        # Thinking Phase
        print("\n--- Phase 1: Thinking ---")
        for persona, thinking in result.thinking_results.items():
            print(f"\n[{persona.upper()}]")
            print(thinking.content.strip())

        # Debate Phase
        if result.debate_results:
            print("\n--- Phase 2: Debate ---")
            for round_data in result.debate_results:
                print(f"\n[Round {round_data.round_number}]")
                for persona, output in round_data.outputs.items():
                    content = (
                        list(output.responses.values())[0] if output.responses else ""
                    )
                    print(
                        f"  {persona.value.upper()}: {content[:100]}..."
                        if not verbose
                        else f"\n[{persona.value.upper()}]\n{content}"
                    )

        # Voting Phase
        print("\n--- Phase 3: Voting ---")
        for persona, vote in result.voting_results.items():
            print(f"[{persona.value.upper()}]: {vote.vote.value.upper()}")
            print(f"  Reason: {vote.reason}")
            if vote.conditions:
                print(f"  Conditions: {', '.join(vote.conditions)}")

        print("\n" + "=" * 60)
        print(f"Exit Code: {result.exit_code}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="MAGI Gemini Orchestrator CLI")
    parser.add_argument("query", help="Query or topic for MAGI system")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    try:
        asyncio.run(run_magi(args.query, args.verbose))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(130)


if __name__ == "__main__":
    main()
