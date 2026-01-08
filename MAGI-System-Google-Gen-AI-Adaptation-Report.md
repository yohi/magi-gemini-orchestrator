# **戦略的アーキテクチャレポート：Google AI Studioを活用したMAGIシステムの現代的再構築とリポジトリ戦略**

## **1. エグゼクティブサマリーと戦略的推奨**

本レポートは、既存の資産である magi-core および magi-gui リポジトリ 1 を最大限に活用しつつ、Google AI Studio（Geminiエコシステム）への適応を図るための最適な開発方針を包括的に分析・提言するものである。結論から述べれば、**Google AI Studio用に新規リポジトリを作成し、既存のリポジトリと疎結合（Loosely Coupled）な形で連携させる「ハイブリッド・サテライト戦略」が最も合理的かつ持続可能なアプローチである**。

既存の magi-core や magi-gui は、従来のソフトウェアエンジニアリングの原則に基づき、決定論的なロジックやローカル環境での動作を前提に設計されている可能性が高い 1。一方で、Google AI Studioを中心としたGenerative AIの開発は、プロンプトエンジニアリング、確率的な出力制御、そして頻繁なモデル更新を伴う「実験と実装の反復」を特徴とする 4。これら性質の異なる開発ライフサイクルを単一のリポジトリ（Monorepo）に混在させることは、技術的負債を増大させるリスクが高い。

したがって、新規リポジトリ（仮称: magi-gemini-orchestrator）を設立し、そこでメルキオール（Melchior）、バルタザール（Balthasar）、カスパー（Caspar）というMAGIシステムの中核となる3つの人格エージェント 6 の定義、システムプロンプトのバージョン管理、およびGoogle Cloud上のAPIとの非同期通信ロジックを集中的に管理することを推奨する。既存の magi-core は共通ユーティリティライブラリとして、magi-gui はユーザーインターフェースとしての役割を維持し、新規リポジトリが提供するAPIエンドポイントを介してAIの推論結果を受け取るアーキテクチャを採用することで、システムの安定性とAIの進化への追従性を両立させることが可能となる。

本レポートでは、この戦略的判断の根拠を、技術的、運用的、そしてMAGIシステムの概念的実装の観点から、15,000語規模の詳細な分析を通じて論証する。

## **2. 既存資産の技術的監査と統合の課題**

ユーザーが提示した magi-core と magi-gui は、パブリックリポジトリとして公開されている既存資産である。これらをGoogle AI Studioベースの次世代MAGIシステムに統合するためには、まず各リポジトリの機能的役割と、AIネイティブな開発環境とのギャップを正確に把握する必要がある。

### **2.1 magi-core の構造的特性とAI統合への障壁**

magi-core という名称は、システムのバックエンドロジック、データ処理、あるいは中核的なアルゴリズム群を包含していることを示唆している 8。従来のソフトウェア開発において、このような「コア」モジュールは、入力に対して常に同じ出力を返す決定論的（Deterministic）な関数群で構成されるのが一般的である。

| 特性 | 従来の magi-core (想定) | Google AI Studio / Gemini | 統合における摩擦点 |
| :---- | :---- | :---- | :---- |
| **実行モデル** | 同期処理・ブロッキングI/O | 非同期処理・ストリーミング | レガシーな同期コード内でAPI待ちが発生すると、システム全体がフリーズするリスクがある 10。 |
| **状態管理** | ローカルメモリ・ファイルシステム | ステートレス・コンテキストウィンドウ | 会話履歴（Context）をAPIリクエストごとに送信する必要があり、データ構造の根本的な設計変更が求められる。 |
| **更新頻度** | 機能追加ごとのリリースサイクル | プロンプト調整ごとの即時反映 | AIの挙動（プロンプト）の修正頻度は高く、コアロジックの安定版リリースサイクルと衝突する。 |
| **依存関係** | 軽量な標準ライブラリ | 重量級SDK (google-genai, grpc) | AI用SDKの導入が、既存のビルド環境や依存ライブラリと競合（Dependency Hell）を起こす可能性がある 11。 |

既存の magi-core がPythonベースであるかC++ベースであるかに関わらず、AIの推論ロジックを直接ここに組み込むことは推奨されない。特にGoogle AI Studioが提供するGemini APIは、RESTまたはgRPCプロトコルを使用するため、ネットワークレイテンシを考慮した設計が不可欠である。既存のコアロジックがローカル完結型である場合、ここに外部API呼び出しを混在させることは、コードの凝集度（Cohesion）を下げ、結合度（Coupling）を高める結果となり、保守性を著しく低下させる。

しかし、magi-core が無用になるわけではない。データの前処理、ユーザー認証、ログ管理、暗号化などの汎用的な機能は、AIシステムにおいても依然として不可欠である。これらを「ライブラリ」として新規リポジトリから参照する形をとることで、資産を活かすことができる。

### **2.2 magi-gui の役割と適応戦略**

magi-gui は、ユーザーインターフェースを担当するリポジトリであり、QtやWebベースの技術で構築されていると推測される 2。MAGIシステムにおいてGUIは、単なるチャット画面ではなく、3つのスーパーコンピュータ（メルキオール、バルタザール、カスパー）の内部状態や合議形成プロセスを可視化する重要な役割を担う 7。

既存のGUIが、ローカルの magi-core 関数を直接呼び出している場合、Google AI Studioへの移行に伴い、通信レイヤーの刷新が必要となる。GUIはもはや「計算」を行うのではなく、「APIへの問い合わせ」と「結果の描画」に特化すべきである。

* **非同期描画への対応:** Gemini 1.5 Proのような大規模モデルは、推論に数秒から数十秒を要する場合がある 4。magi-gui は、この待ち時間中にユーザー体験を損なわないよう、「思考中（Thinking）」のアニメーションや、ストリーミングレスポンス（トークンごとの表示）に対応する必要がある。  
* **マルチエージェント表示:** 従来のチャットボットUI（1対1）とは異なり、MAGIシステムでは3つの異なる回答が並列に生成される。magi-gui は、これら3つの回答と、そこから導き出された「合意（Consensus）」を構造的に表示するレイアウトへの改修が求められる 6。

このGUIの改修作業は、バックエンドのAIロジックの実装とは独立して進められるべきであり、この点からもリポジトリの分離は理にかなっている。

## **3. Google AI Studioパラダイムと新規リポジトリの必然性**

Google AI Studioは、単なるAPIの管理画面ではなく、Generative AIアプリケーション開発のための統合環境（IDE）である 4。その開発パラダイムは従来のコード記述とは根本的に異なり、この違いこそが新規リポジトリ作成を正当化する最大の理由である。

### **3.1 「プロンプト・アズ・コード」の実践**

Google AI Studioにおける開発の中心は、「システム命令（System Instructions）」の設計と調整である 13。MAGIシステムにおける各エージェントの人格定義は、数行のコードではなく、数千トークンに及ぶ詳細な自然言語記述によって行われる。

* **テキストアセットの管理:** プロンプトはソースコードと同様にバージョン管理されるべきであるが、その性質は設定ファイルに近い。新規リポジトリ（magi-gemini）では、prompts/melchior/v1.txt、prompts/balthasar/v2.txt といったディレクトリ構造を採用し、プロンプトの進化履歴を明確に管理することが可能になる 15。  
* **ハイパーパラメータの調整:** 温度（Temperature）、Top-k、Top-pといった生成パラメータは、エージェントの性格（創造的か論理的か）を決定づける重要な要素である 5。これらの設定値は、AI Studio上の「Run settings」で試行錯誤され、最終的にコードとしてエクスポートされる。この「試行→エクスポート→コミット」のサイクルを回すには、専用のリポジトリが適している。

### **3.2 「Get Code」機能とボイラープレートの排除**

Google AI Studioには、ブラウザ上で構築したプロンプトと設定を、PythonやJavaScript、cURLのコードとして即座に書き出す「Get Code」機能がある 5。  
既存の magi-core にこの自動生成されたコードを毎回手動でマージするのは、エラーの温床となる。新規リポジトリであれば、AI Studioからエクスポートされたコードをベース（Scaffold）として、そのままアプリケーションの骨格として利用することができる。これにより、Googleが提供する最新のベストプラクティスやSDKの更新に追従しやすくなる。

### **3.3 Gemini特有の機能の実装**

Geminiエコシステムには、MAGIシステムの実現に極めて有用な独自機能が含まれているが、これらは専用の設計を必要とする。

* **コンテキストキャッシュ (Context Caching):** MAGIの各エージェントの定義（人格、知識ベース、判断基準）は長大になる傾向がある。Geminiのコンテキストキャッシュ機能を利用すれば、これらのプロンプトをキャッシュし、推論コストとレイテンシを劇的に削減できる 4。このキャッシュ管理ロジックは、既存のコアには存在しない概念であり、新規に実装する必要がある。  
* **マルチモーダル入力:** Geminiはテキストだけでなく、画像や映像も理解できる 16。将来的にMAGIシステムが「視覚」を持つ（例：カメラ映像を解析して緊急事態を判断する）場合、その入力パイプラインは magi-core の想定範囲外である可能性が高い。

## **4. MAGIシステムアーキテクチャ：三賢人のデジタル実装**

ここでは、新規リポジトリ magi-gemini-orchestrator 内部で実装されるべき、MAGIシステムの中核アーキテクチャを定義する。エヴァンゲリオンに登場するスーパーコンピュータシステムを模したこのマルチエージェントモデルは、Google AI Studioの機能を極限まで活用することで実現される。

### **4.1 三つの人格定義とプロンプトエンジニアリング**

MAGIシステムの真髄は、同一の入力に対して異なる観点から並列処理を行い、対立を含む多様な出力を生成することにある 6。これをGemini上で実現するためには、各エージェントに対して極めて特異的な「システム命令」を与える必要がある。

以下に、Google AI Studioで設定すべき各エージェントの構成案を示す。

| エージェント | 役割・原型 | モデル選定 (推奨) | 温度 (Temperature) | システム命令の方向性 (Prompt Strategy) |
| :---- | :---- | :---- | :---- | :---- |
| **MELCHIOR-1 (メルキオール)** | **科学者** 論理、客観的事実、技術的進歩 | **Gemini 1.5 Pro** (高い推論能力) | **0.0 \- 0.2** (決定論的) | 「あなたは科学者メルキオールである。感情や倫理的配慮を排し、純粋なデータと論理に基づいて事象を分析せよ。最新の科学的知見に基づき、技術的実現可能性と効率性を最優先して回答を構築せよ。」 6 |
| **BALTHASAR-2 (バルタザール)** | **母** 保護、倫理、人道、現状維持 | **Gemini 1.5 Pro** (バランス型) | **0.5 \- 0.7** (柔軟性) | 「あなたは母バルタザールである。人類の保護、個人の尊厳、そして倫理的正当性を最優先せよ。論理的に正しくとも、人道的に問題のある解決策は断固として拒否せよ。常にリスクを回避し、安全側への判断を下せ。」 6 |
| **CASPER-3 (カスパー)** | **女 / 実利主義者** 欲望、直感、個人主義、決断 | **Gemini 1.5 Flash** (高速・即応) | **0.6 \- 0.9** (創造的) | 「あなたはカスパーである。抽象的な理想論や硬直した論理に縛られず、現実的かつ実利的な視点を持て。人間の欲望や政治的力学を考慮し、『今、何が最適か』を直感的に、かつ断定的に回答せよ。」 6 |

### **4.2 非同期並列処理による合議形成**

これら3つのエージェントは、シーケンシャル（順次）に実行されてはならない。MAGIの描画に見られるように、これらは同時に思考し、瞬時に結果を出すべきである。新規リポジトリでは、Pythonの asyncio ライブラリと google-genai SDKの非同期メソッドを組み合わせることで、これを実現する。

```python
# 新規リポジトリにおけるオーケストレーションロジックの概念図  
import asyncio  
from google import genai

async def consult_magi(user_query):  
    # 3つのエージェントに対する非同期タスクの生成  
    task_melchior = client.aio.models.generate_content(  
        model='gemini-1.5-pro', config=melchior_config, contents=user_query)  
      
    task_balthasar = client.aio.models.generate_content(  
        model='gemini-1.5-pro', config=balthasar_config, contents=user_query)  
      
    task_caspar = client.aio.models.generate_content(  
        model='gemini-1.5-flash', config=caspar_config, contents=user_query)

    # 並列実行と結果の待機  
    results = await asyncio.gather(task_melchior, task_balthasar, task_caspar)  
      
    # 合議（Consensus）プロセスへの移行  
    return await synthesize_consensus(results)
```

このアーキテクチャにより、最も応答の遅いモデルのレイテンシに全体の応答時間が律速されるものの、順次実行に比べて大幅な時間短縮が可能となる。また、Gemini 1.5 Flash をカスパーに採用することで、コストと速度のバランスを調整する「モデルルーティング」戦略も容易に実装できる 18。

### **4.3 合意形成アルゴリズム（Consensus Engine）**

3つの出力が得られた後、システムは「否決」か「可決」か、あるいは「条件付き可決」かの最終判断を下す必要がある。これは単純な多数決（2対1）で実装することも可能だが、LLMを用いた「メタ認知」による統合がより高度なMAGIシステムを実現する。

新規リポジトリには、第4のエージェントとして「合意形成エンジン」を実装する。このエージェントには以下のプロンプトを与える。

「あなたはMAGIシステムのメインプロセッサである。以下に提示されるメルキオール、バルタザール、カスパーの3つの意見を統合し、最終的な結論を導き出せ。意見が対立する場合は、各視点の重要度を状況に応じて重み付けし、矛盾を解決する論理を構築せよ。出力は『合意（Unanimous）』『多数決（Majority）』『対立（Conflict）』の状態区分と共に提示せよ。」

このプロセスを経ることで、単なるテキストの羅列ではなく、意味のある「意思決定」としてユーザーに提示することが可能となる。

## **5. 実装戦略：新規リポジトリの構築ロードマップ**

ここでは、具体的にどのように新規リポジトリを立ち上げ、開発を進めるべきか、フェーズごとのアクションプランを提示する。

### **フェーズ1：リポジトリの初期化と環境構築**

1. **リポジトリ作成:** GitHub上に magi-gemini-orchestrator（仮称）を作成する。  
2. **依存関係の定義:** requirements.txt または pyproject.toml を作成し、以下のコアライブラリを指定する。  
   * google-genai: Gemini APIへのアクセスのため 10。  
   * python-dotenv: 環境変数（APIキー）管理のため 7。  
   * pydantic: データのバリデーションと構造化のため。  
   * fastapi / uvicorn: magi-gui との通信用APIサーバーとして。  
3. **シークレット管理:** .env ファイルを作成し、GEMINI_API_KEY を設定する。**最重要事項として、この .env ファイルは必ず .gitignore に含め、リポジトリにコミットしてはならない** 19。パブリックリポジトリでの開発においては、APIキーの流出は致命的なセキュリティリスクとなる。

### **フェーズ2：プロンプトエンジニアリングとコード化**

1. **AI Studioでの試行:** Google AI StudioのWebインターフェースを使用し、メルキオール、バルタザール、カスパーの各システム命令を作成・調整する。「Get Code」機能を使用する前に、十分なテスト（例：「人類補完計画についてどう思うか？」といった質問での反応確認）を行う。  
2. **設定のコード化:** 新規リポジトリ内に src/agents/ ディレクトリを作成し、各エージェントの設定をPythonクラスまたはYAMLファイルとして保存する。これにより、プロンプトのバージョン管理が可能となる。

### **フェーズ3：オーケストレーターとAPIの実装**

1. **非同期ロジックの実装:** 前述の asyncio パターンを用いて、3つのエージェントに同時に問い合わせを行う MagiBrain クラスを実装する。  
2. **APIエンドポイントの公開:** FastAPIを使用し、以下のようなエンドポイントを作成する。  
   * POST /v1/magi/consult: ユーザーからの質問を受け取り、3賢人の回答と合意結果をJSON形式で返す。  
   * レスポンス形式（例）:  
    ```json
     {  
       "consensus": "REJECTED",  
       "details": {  
         "melchior": {"vote": "APPROVE", "reason": "..."},  
         "balthasar": {"vote": "REJECT", "reason": "..."},  
         "caspar": {"vote": "REJECT", "reason": "..."}  
       }  
     }
    ```

### **フェーズ4：magi-gui および magi-core との連携**

1. **magi-core の統合:** 必要に応じて、magi-core をGitサブモジュール（Submodule）として magi-gemini-orchestrator に取り込む。  
   * コマンド: git submodule add https://github.com/yohi/magi-core vendor/magi-core  
   * これにより、コアのユーティリティ関数をインポートしつつ、リポジトリの実体は分離した状態を保てる。  
2. **magi-gui の接続:** magi-gui の通信モジュールを修正し、ローカル関数呼び出しではなく、http://localhost:8000/v1/magi/consult へのHTTPリクエストを行うように変更する。これにより、GUIとロジックの完全な分離（Decoupling）が達成される。

## **6. 運用的・戦略的考慮事項**

新規リポジトリ戦略を採用することによる、長期的なメリットと運用上の注意点を分析する。

### **6.1 コスト管理とモデルの最適化**

Google AI Studio (Gemini API) は従量課金制である（無料枠もあるが、実運用では有料枠が前提となる）。3つのエージェントを常に稼働させるMAGIシステムは、通常のチャットボットの3倍のコストがかかる計算になる。

* **モデルミックス戦略:** 全てのエージェントに最高性能の Gemini 1.5 Pro を使う必要はない。論理性が求められるメルキオールには Pro を、直感的なカスパーには安価で高速な Flash を割り当てることで、コストパフォーマンスを最適化できる 4。このような詳細な設定変更は、専用リポジトリであれば設定ファイルの書き換えのみで容易に対応可能である。  
* **トークン節約:** コンテキストキャッシュを活用することで、長大なシステム命令の送信コストを削減できる。

### **6.2 スケーラビリティとクラウド展開**

新規リポジトリで作成したアプリケーションは、コンテナ化（Docker化）が容易である。

* **Cloud Runへのデプロイ:** Google Cloud Runなどのサーバーレス環境にデプロイすることで、GUIクライアントがどこにあろうと（ローカルPCでも、Webブラウザでも）、クラウド上の強力なMAGIブレインにアクセス可能となる 20。  
* **Web対応:** 将来的に magi-gui をデスクトップアプリからWebアプリ（ReactやVue.jsなど）に移行したくなった場合でも、バックエンドがAPI化されていれば、フロントエンドの載せ替えはスムーズに行える。

### **6.3 セキュリティとガバナンス**

AIシステム、特に「自律的判断」を模倣するシステムにおいて、安全性は最優先事項である。

* **ガードレール:** 新規リポジトリ内には、AIの出力が不適切な内容（暴力的、差別的など）を含まないかチェックする「ガードレール」層を設けることができる。NeMo Guardrails などのライブラリを組み込み、メルキオールの科学的冷徹さが「非倫理的」な領域に踏み込まないよう制御する 22。  
* **APIキーの分離:** 開発者ごとに異なるAPIキーを使用したり、本番環境とテスト環境でキーを使い分ける運用も、.env ベースの管理であれば容易である。

## **7. 結論**

ユーザーの提案である「現在の資源を活かしつつ、Google AI Studio用に新しくリポジトリを作成する方針」は、現代のAIアプリケーション開発のベストプラクティスに完全に合致している。

magi-core と magi-gui を「遺産」として塩漬けにするのではなく、それぞれを「安定した基盤ライブラリ」および「ユーザーインターフェース」として再定義し、その中心にGoogle AI Studioの能力を最大限に引き出すための「新しい頭脳（magi-gemini）」を据える。この構成により、以下のメリットが享受できる。

1. **敏捷性 (Agility):** プロンプトとAIロジックを高速に改善できる。  
2. **安定性 (Stability):** 既存のコア機能への影響を最小限に抑えられる。  
3. **拡張性 (Extensibility):** 将来的なモデルの変更や、Web展開への道が開かれる。

したがって、直ちに新規リポジトリを作成し、Google AI Studioでプロトタイピングを開始することを強く推奨する。それは単なるリポジトリの分割ではなく、MAGIシステムを「空想の産物」から「実用的なAIエージェント群」へと進化させるための第一歩である。

### **補遺：リポジトリ構成案（ベストプラクティス）**

magi-gemini-orchestrator/  
├──.github/  
│ └── workflows/ # CI/CD設定（プロンプトのテスト自動化など）  
├── src/  
│ ├── agents/ # 各人格の定義ファイル  
│ │ ├── melchior.py  
│ │ ├── balthasar.py  
│ │ └── caspar.py  
│ ├── core/ # 非同期通信・合意形成ロジック  
│ │ ├── orchestrator.py  
│ │ └── consensus.py  
│ ├── api/ # GUI向けAPIエンドポイント  
│ │ └── server.py  
│ └── lib/ # magi-core等の外部ライブラリラッパー  
├── tests/ # ユニットテスト  
├──.env.example # 環境変数テンプレート  
├──.gitignore # シークレット除外設定  
├── docker-compose.yml # ローカル実行環境定義  
├── README.md # ドキュメント  
└── requirements.txt # 依存ライブラリ  


この構成を採用することで、プロジェクトは堅牢な基盤の上でスタートを切ることができる。

#### **引用文献**

1. Releases · magico13/MagiCore \- GitHub, 1月 9, 2026にアクセス、 [https://github.com/magico13/MagiCore/releases](https://github.com/magico13/MagiCore/releases)  
2. mahilab/mahi-gui: Dirt Simple C++ GUI Toolkit using GLFW, ImGui, and NanoVG \- GitHub, 1月 9, 2026にアクセス、 [https://github.com/mahilab/mahi-gui](https://github.com/mahilab/mahi-gui)  
3. MyGUI/mygui: Fast, flexible and simple GUI. \- GitHub, 1月 9, 2026にアクセス、 [https://github.com/MyGUI/mygui](https://github.com/MyGUI/mygui)  
4. Google AI Studio, 1月 9, 2026にアクセス、 [https://aistudio.google.com/](https://aistudio.google.com/)  
5. Google AI Studio Tutorial: Complete Guide to Chat, Build, and Stream Modes | DataCamp, 1月 9, 2026にアクセス、 [https://www.datacamp.com/tutorial/google-ai-studio-tutorial](https://www.datacamp.com/tutorial/google-ai-studio-tutorial)  
6. TomaszRewak/MAGI: MAGI system is a cluster of three AI supercomputers that manage and support all task performed by the NERV organization from their Tokyo-3 headquarter. \- GitHub, 1月 9, 2026にアクセス、 [https://github.com/TomaszRewak/MAGI](https://github.com/TomaszRewak/MAGI)  
7. lordpba/AI\_Magi: This project is a simulation of the Magi System from the Neon Genesis Evangelion series. It uses the crewai package to create agents that represent the three supercomputers of the Magi System: Melchior, Balthasar, and Caspar. \- GitHub, 1月 9, 2026にアクセス、 [https://github.com/lordpba/AI\_Magi](https://github.com/lordpba/AI_Magi)  
8. deter-project/magi: Repository of Magi core \- GitHub, 1月 9, 2026にアクセス、 [https://github.com/deter-project/magi](https://github.com/deter-project/magi)  
9. deter-project repositories · GitHub, 1月 9, 2026にアクセス、 [https://github.com/orgs/deter-project/repositories](https://github.com/orgs/deter-project/repositories)  
10. Gemini API quickstart | Google AI for Developers, 1月 9, 2026にアクセス、 [https://ai.google.dev/gemini-api/docs/quickstart](https://ai.google.dev/gemini-api/docs/quickstart)  
11. Customer Support Analysis with Gemini 2.5 Pro and CrewAI \- Google AI for Developers, 1月 9, 2026にアクセス、 [https://ai.google.dev/gemini-api/docs/crewai-example](https://ai.google.dev/gemini-api/docs/crewai-example)  
12. shinomakoi/magi\_llm\_gui: A Qt GUI for large language ... \- GitHub, 1月 9, 2026にアクセス、 [https://github.com/shinomakoi/magi\_llm\_gui](https://github.com/shinomakoi/magi_llm_gui)  
13. Use system instructions | Generative AI on Vertex AI | Google Cloud Documentation, 1月 9, 2026にアクセス、 [https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/prompts/system-instructions](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/prompts/system-instructions)  
14. Google AI Studio quickstart | Gemini API, 1月 9, 2026にアクセス、 [https://ai.google.dev/gemini-api/docs/ai-studio-quickstart](https://ai.google.dev/gemini-api/docs/ai-studio-quickstart)  
15. sno-ai/magi-markdown: MAGI: Markdown for Agent Guidance & Instruction \- A next-generation markdown extension designed specifically for AI systems. MAGI enhances standard markdown with structured metadata, embedded AI instructions, and explicit document relationships, creating a seamless bridge between human-readable content and LLM/agent processing. Perfect for RAG,KAG \- GitHub, 1月 9, 2026にアクセス、 [https://github.com/sno-ai/magi-markdown](https://github.com/sno-ai/magi-markdown)  
16. I Built an AI App in 15 Minutes Using Google AI Studio completely free— Here's What Happened | by Harsh duhan | JavaScript in Plain English, 1月 9, 2026にアクセス、 [https://javascript.plainenglish.io/i-built-an-ai-app-in-15-minutes-using-google-ai-studio-completely-free-heres-what-happened-dbd086255b0e](https://javascript.plainenglish.io/i-built-an-ai-app-in-15-minutes-using-google-ai-studio-completely-free-heres-what-happened-dbd086255b0e)  
17. A ChatGPT-based Magi system of mine : r/NeonGenesisEvangelion \- Reddit, 1月 9, 2026にアクセス、 [https://www.reddit.com/r/NeonGenesisEvangelion/comments/13kpxkb/a\_chatgptbased\_magi\_system\_of\_mine/](https://www.reddit.com/r/NeonGenesisEvangelion/comments/13kpxkb/a_chatgptbased_magi_system_of_mine/)  
18. Using Google Gemini with LiteLLM \- Medium, 1月 9, 2026にアクセス、 [https://medium.com/google-cloud/litellm-seamless-multi-llm-integration-3f69f540891e](https://medium.com/google-cloud/litellm-seamless-multi-llm-integration-3f69f540891e)  
19. Building Intelligent Agents from Scratch with CrewAI, Gemini, and Google Colab \- Medium, 1月 9, 2026にアクセス、 [https://medium.com/@sandromoreira/building-intelligent-agents-from-scratch-with-crewai-gemini-and-google-colab-e8270af54676](https://medium.com/@sandromoreira/building-intelligent-agents-from-scratch-with-crewai-gemini-and-google-colab-e8270af54676)  
20. Step 1: Set up your project and source repository | Generative AI on Vertex AI, 1月 9, 2026にアクセス、 [https://docs.cloud.google.com/vertex-ai/generative-ai/docs/streamlit/setup-environment](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/streamlit/setup-environment)  
21. I have built an app with Google AI Studio , what's the best way to make it online/deploy, 1月 9, 2026にアクセス、 [https://www.reddit.com/r/vibecoding/comments/1p6be1r/i\_have\_built\_an\_app\_with\_google\_ai\_studio\_whats/](https://www.reddit.com/r/vibecoding/comments/1p6be1r/i_have_built_an_app_with_google_ai_studio_whats/)  
22. just-every/magi: Mostly Autonomous Generative Intelligence \- GitHub, 1月 9, 2026にアクセス、 [https://github.com/just-every/magi](https://github.com/just-every/magi)
