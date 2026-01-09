# Google AI Studio セットアップ & ワークフロー

## はじめに
Google AI Studio は、MAGI システムの各エージェント（メルキオール、バルタザール、カスパー）のプロンプトを迅速にプロトタイピングし、調整するための強力なツールです。本リポジトリ `magi-gemini-orchestrator` では、Google AI Studio で洗練させたプロンプトをコードに反映させるワークフローを推奨しています。

## アカウントとAPIキーの設定
1. [Google AI Studio](https://aistudio.google.com/) にアクセスし、Google アカウントでサインインします。
2. 左側のサイドバーにある **"Get API key"** をクリックします。
3. **"Create API key in new project"** をクリックして新しい API キーを生成します（既存のプロジェクトがある場合はそちらを選択しても構いません）。
4. 生成された API キーをコピーします。
5. 本リポジトリのルートディレクトリにある `.env` ファイルを開き（存在しない場合は `.env.example` をコピーして作成）、以下の環境変数に値を設定します。
   ```env
   MAGI_GEMINI_API_KEY=あなたのAPIキー
   ```
   ※ セットアップの詳細は `README.md` を参照してください。

## ワークフロー：MAGI エージェントのチューニング
エージェントの振る舞いを調整する際は、以下のステップで行うことを推奨します。

1. **システム命令の取得**:
   調整したいエージェントの Python ファイル（例: `src/magi_orchestrator/agents/melchior.py`）を確認し、`system_instruction` に渡されているプロンプト文字列をコピーします。
   ※ 多くのプロンプトは `magi-core` ライブラリ（`magi.agents.persona`）からインポートされています。

2. **Google AI Studio での新規プロンプト作成**:
   - Google AI Studio で **"Create New"** > **"Chat Prompt"** を選択します。
3. **システム命令の貼り付け**:
   - 画面上部の **"System Instructions"** ボックスに、コピーした命令を貼り付けます。
4. **テストの実行**:
   - チャットインターフェースで、エージェントへのサンプルクエリ（例: 「このアーキテクチャの妥当性を分析せよ」）を入力し、応答を確認します。
5. **パラメータの調整**:
   - 右側のパネルで、エージェントのペルソナに合わせて **Temperature** を調整します。
     - **MELCHIOR (論理・科学)**: 0.2 (決定論的)
     - **BALTHASAR (倫理・保護)**: 0.5 (バランス)
     - **CASPER (欲望・実利)**: 0.8 (創造的)
   - 必要に応じて Safety Settings や Top-P などの設定も調整します。
6. **コードへの反映**:
   - Studio 上で最適な応答が得られたら、洗練されたプロンプトや設定値を Python コードに書き戻します。

## モデルの選択
Google AI Studio では、利用可能な最新モデル（Gemini 1.5 Pro, Gemini 1.5 Flash, Gemini 2.0 Flash など）を切り替えてテストできます。
- **Gemini 1.5 Pro**: 高度な論理推論が必要なエージェントに適しています。
- **Gemini 1.5/2.0 Flash**: 高速な応答や、直感的な判断が求められるエージェントに適しています。

各エージェントが使用するモデルは、各エージェントの設定ファイル（`src/magi_orchestrator/agents/*.py`）の `model` パラメータで指定します。

## 便利なリンク
- [Google AI Studio](https://aistudio.google.com/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Gemini API Pricing](https://ai.google.dev/pricing)
