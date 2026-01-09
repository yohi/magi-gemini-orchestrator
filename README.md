# MAGI Gemini Orchestrator

<div align="center">

![MAGI System Logo](https://img.shields.io/badge/MAGI-Gemini-purple?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Version](https://img.shields.io/badge/Version-0.1.0-orange?style=flat-square)

**google-genai SDK ネイティブの MAGI システム実装**

</div>

---

## 概要

`magi-gemini-orchestrator` は、Google Gemini API の公式 SDK（`google-genai`）を使用した MAGI システムの軽量実装です。

3賢者（MELCHIOR、BALTHASAR、CASPER）による合議プロセスを通じて、多角的で信頼性の高い判断を提供します。

### 特徴

- 🚀 **google-genai SDK ネイティブ**: 最新の Google Gen AI SDK を使用
- ⚡ **非同期並列実行**: `asyncio.gather` による3エージェント同時実行
- 💾 **コンテキストキャッシュ対応**: ペルソナ定義をキャッシュしてコスト削減
- 🔧 **magi-core 依存**: 既存の ConsensusResult/Vote 等のモデルを再利用

---

## アーキテクチャ

```
magi-gemini-orchestrator (この新リポジトリ)
├── GeminiNativeClient     # google-genai SDK ラッパー
├── MagiOrchestrator       # 合議プロセス制御
├── CacheManager           # コンテキストキャッシュ管理
└── agents/                # 3賢者設定
    ├── melchior.py        # 論理・科学 (temp=0.2)
    ├── balthasar.py       # 倫理・保護 (temp=0.5)
    └── casper.py          # 欲望・実利 (temp=0.8)

↓ 依存

magi-core
├── PersonaType, Vote, Decision  # 共通 Enum
├── ThinkingOutput, VoteOutput   # データ構造
├── ConsensusResult              # 最終結果
└── MELCHIOR_BASE_PROMPT, etc.   # ペルソナ定義
```

---

## インストール

### 前提条件

- Python 3.11 以上
- [uv](https://github.com/astral-sh/uv) パッケージマネージャー（推奨）

### セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/yohi/magi-gemini-orchestrator.git
cd magi-gemini-orchestrator

# 環境変数を設定
cp .env.example .env
# .env を編集して MAGI_GEMINI_API_KEY を設定
# （詳細なセットアップ手順は [GOOGLE_AI_STUDIO_SETUP.md](./GOOGLE_AI_STUDIO_SETUP.md) を参照）

# 依存関係をインストール
uv sync
```

---

## 使用方法

### 基本的な使い方

```python
import asyncio
from magi_orchestrator import GeminiNativeClient, MagiOrchestrator

async def main():
    # クライアントを作成
    client = GeminiNativeClient(api_key="your-gemini-api-key")
    
    # オーケストレーターを作成
    orchestrator = MagiOrchestrator(client)
    
    # 3賢者に問い合わせ
    result = await orchestrator.consult(
        "このマイクロサービスアーキテクチャは適切ですか？"
    )
    
    # 結果を表示
    print(f"最終判定: {result.final_decision.value}")
    print(f"終了コード: {result.exit_code}")
    
    # 各エージェントの思考を表示
    for persona_name, thinking in result.thinking_results.items():
        print(f"\n【{persona_name.upper()}の分析】")
        print(thinking.content)

    # 議論結果を表示
    for round_data in result.debate_results:
        print(f"\n【Debate Round {round_data.round_number}】")
        for persona_type, output in round_data.outputs.items():
            # 最初のレスポンスを表示
            content = list(output.responses.values())[0] if output.responses else ""
            print(f"[{persona_type.value.upper()}]: {content[:100]}...")

    # 投票結果を表示
    for persona_type, vote in result.voting_results.items():
        print(f"\n【{persona_type.value.upper()}の投票】")
        print(f"  投票: {vote.vote.value}")
        print(f"  理由: {vote.reason}")

asyncio.run(main())
```

### 設定のカスタマイズ

```python
from magi_orchestrator import OrchestratorSettings, GeminiNativeClient, MagiOrchestrator

# 設定を読み込み（環境変数/.env から）
settings = OrchestratorSettings()

# または明示的に設定
settings = OrchestratorSettings(
    api_key="your-api-key",
    default_model="gemini-2.0-flash",
    voting_threshold="unanimous",  # 全員一致が必要
)

client = GeminiNativeClient(
    api_key=settings.api_key,
    timeout=settings.timeout,
)

orchestrator = MagiOrchestrator(
    client,
    voting_threshold=settings.voting_threshold,
)
```

### コンテキストキャッシュの使用

```python
from google import genai
from magi_orchestrator import CacheManager, GeminiNativeClient, MagiOrchestrator

# キャッシュマネージャーを作成
cache_client = genai.Client(api_key="your-api-key")
cache_manager = CacheManager(cache_client)

# 全ペルソナのキャッシュを事前作成
cache_manager.warmup_all_personas(
    model="gemini-2.0-flash",
    ttl_seconds=3600,
)

# キャッシュを使用してオーケストレーターを作成
orchestrator = MagiOrchestrator(
    client=GeminiNativeClient(api_key="your-api-key"),
    cache_manager=cache_manager,
)

# 2回目以降のリクエストでキャッシュが効く
result = await orchestrator.consult("質問内容")
```

---

## 環境変数

| 変数名 | 説明 | デフォルト |
|--------|------|-----------|
| `MAGI_GEMINI_API_KEY` | Gemini API Key（**必須**） | - |
| `MAGI_GEMINI_DEFAULT_MODEL` | 使用するモデル | `gemini-2.0-flash` |
| `MAGI_GEMINI_VOTING_THRESHOLD` | 投票閾値（majority/unanimous） | `majority` |
| `MAGI_GEMINI_CACHE_TTL_SECONDS` | キャッシュ有効期限（秒） | `3600` |
| `MAGI_GEMINI_TIMEOUT` | API タイムアウト（秒） | `60` |

---

## 3賢者の設定

| エージェント | 役割 | Temperature | 説明 |
|-------------|------|-------------|------|
| **MELCHIOR-1** | 論理・科学 | 0.2 | 決定論的で論理的な分析 |
| **BALTHASAR-2** | 倫理・保護 | 0.5 | バランスの取れたリスク評価 |
| **CASPER-3** | 欲望・実利 | 0.8 | 創造的で実践的な提案 |

---

## 投票結果と終了コード

| 投票結果 | Exit Code | 説明 |
|---------|-----------|------|
| APPROVED | 0 | 過半数（または全員）が承認 |
| DENIED | 1 | 過半数（または全員）が否決 |
| CONDITIONAL | 2 | 条件付き承認 |

---

## 開発

### テストの実行

```bash
# ユニットテスト
uv run pytest tests/ -v

# カバレッジ付き
uv run pytest tests/ --cov=src/magi_orchestrator --cov-report=html
```

### プロジェクト構造

```
magi-gemini-orchestrator/
├── src/
│   └── magi_orchestrator/
│       ├── __init__.py         # パッケージ初期化
│       ├── config.py           # Pydantic 設定
│       ├── client.py           # GeminiNativeClient
│       ├── orchestrator.py     # MagiOrchestrator
│       ├── cache.py            # CacheManager
│       └── agents/
│           ├── __init__.py
│           ├── base.py         # AgentConfig
│           ├── melchior.py     # MELCHIOR 設定
│           ├── balthasar.py    # BALTHASAR 設定
│           └── casper.py       # CASPER 設定
├── tests/
│   ├── __init__.py
│   └── test_orchestrator.py
├── pyproject.toml
├── .env.example
├── .gitignore
├── README.md
└── MAGI-System-Google-Gen-AI-Adaptation-Report.md
```

---

## ライセンス

MIT License

---

## 関連リンク

- [Google AI Studio](https://aistudio.google.com/)
- [google-genai SDK](https://github.com/googleapis/python-genai)
- [magi-core](https://github.com/yohi/magi-core)

---

<div align="center">

**"The three computers that govern NERV."**

</div>
