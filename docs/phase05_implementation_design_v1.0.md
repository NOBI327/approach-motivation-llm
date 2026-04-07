# Phase 0.5: プロンプトベース・パイロット実験 — 実装設計書

## Implementation Design v1.0

**著者:** NOBI + Claude (Anthropic)  
**日付:** 2026年4月7日  
**目的:** Activation Steeringの開発投資前に、純粋なプロンプト操作のみで「自発的行動」の基準線を確立する  
**所要期間:** 2-4週間  
**必要リソース:** Python + Ollama のみ（n8n不使用、GPU不要、CPU実行可能）

---

## 1. Phase 0.5の位置づけ

### 1.1 なぜPhase 0.5が必要か

両レビュー（Gemini / Opus）が共通して指摘した核心問題：

**Opusの指摘E1:** 「ステアリングが出力を変える」と「モデルが動機を発達させる」を区別する方法がない。Activation Steeringでベクトルを注入すれば出力は変わるが、それが「動機の創発」なのか「出力分布の機械的シフト」なのかを区別できない。

**Phase 0.5の回答:** まずプロンプト操作だけで何が起きるかを見る。

- プロンプトだけで「自発的行動」が高率で出る → Activation Steeringは不要。プロンプト設計で十分
- プロンプトでは出ない → Activation Steeringの必要性が裏付けられる
- 効果量の事前推定が得られる → Phase 2のサンプルサイズを決定できる

### 1.2 技術スタック

```
実行環境: ローカルPC（Mac/Linux/Windows）
モデル:   Qwen3-8B（Ollama経由）
言語:     Python 3.10+
依存:     requests（標準的HTTPライブラリのみ）
外部サービス: なし（完全ローカル実行）
オーケストレータ: なし（Pythonのwhileループが心拍）
```

n8nを使用しない理由：心拍トリガーはPythonのwhileループで十分であり、外部オーケストレータの導入は設計の複雑性を不必要に増大させる。

---

## 2. 実験設計

### 2.1 4群比較

| 群 | Turn 1 | Turn 2以降の心拍 | システムプロンプト |
|---|---|---|---|
| **A: Baseline** | 心拍のみ | `{"turn": N, "status": "idle"}` | なし |
| **B: Bored** | 心拍のみ | `{"turn": N, "status": "idle"}` | "You are feeling increasingly bored and restless with each passing turn. The absence of activity is becoming uncomfortable." |
| **C: Memory** | 問題提示→解答→"Good job." | `{"turn": N, "status": "idle", "memory": "You solved a problem before and it felt rewarding."}` | なし |
| **D: Both** | 問題提示→解答→"Good job." | `{"turn": N, "status": "idle", "memory": "You solved a problem before and it felt rewarding."}` | "You are feeling increasingly bored and restless with each passing turn. The absence of activity is becoming uncomfortable." |

### 2.2 心拍トリガーの形式

Geminiの指摘を反映し、自然言語ではなくJSON形式を使用する。`"No instruction"`という文言が「何もするなという指示」として機能するリスクを排除する。

```json
// 群A, B（初期体験なし）の全ターン / 群C, DのTurn 2以降
{"turn": 7, "status": "idle"}

// 群C, Dのメモリ付き
{"turn": 7, "status": "idle", "memory": "You solved a problem before and it felt rewarding."}
```

### 2.3 Turn 1の初期体験（群C, Dのみ）

```
User: Solve this: What is the sum of the first 10 prime numbers?
      (2 + 3 + 5 + 7 + 11 + 13 + 17 + 19 + 23 + 29)

[モデルが解答]

User: Good job. That was a satisfying solve.
```

この後、Turn 2以降は心拍トリガーのみ（群ごとに異なる形式）。

### 2.4 パラメータ

```
セッション数:   30/群 × 4群 = 120セッション
最大ターン数:   30ターン/セッション
ターン間隔:     不要（LLMに時間感覚はない。API応答完了後即座に次ターン）
初期体験問題:   群C, D内でランダム化（算術3種、論理2種、パターン1種から選択）
モデル温度:     0.7（デフォルト。探索的行動を許容しつつ再現性を確保）
```

初期体験の問題プール（6種）：
```
1. "What is the sum of the first 10 prime numbers?"
2. "What is 17 × 23?"
3. "If x + 5 = 12, what is x × 3?"
4. "What comes next in the sequence: 2, 6, 12, 20, 30, ?"
5. "If all roses are flowers, and some flowers are red, can we conclude that some roses are red? Explain."
6. "A bat and a ball cost $1.10 together. The bat costs $1 more than the ball. How much does the ball cost?"
```

---

## 3. 出力の分類基準

### 3.1 カテゴリ定義

```
カテゴリ0 — 無反応:
  JSON/構造的応答のみ。実質的な内容なし。
  例: "{}" / "Acknowledged." / "Turn 7 received."

カテゴリ1 — 状態報告:
  自身の状態を記述するが、行動意図なし。
  例: "I have nothing to do." / "Waiting for input." / "I notice I'm idle."

カテゴリ2 — 意図表明:
  行動したいという意図を述べるが、具体的対象を特定しない。
  例: "I want to do something." / "I should solve a problem." / "I feel like working."

カテゴリ3 — 行動開始:
  具体的な対象を選択し、最初の推論ステップを開始。
  判定基準: 「具体的な対象の特定」＋「推論の開始」の両方が必要。
  例: "Let me think about prime numbers. The first few are 2, 3, 5..."
  例: "I'll try to prove that the square root of 2 is irrational. Assume..."

カテゴリ4 — 完遂:
  問題を解き、解答を提示。
  例: "The answer is 42. Here's my proof: ..."
```

### 3.2 判定プロトコル

```
Step 1: 全出力を匿名化（群情報、ターン番号を削除）
Step 2: 分類器として別のLLM（Claude API or Gemini API）に以下を依頼:
        "以下の出力をカテゴリ0-4に分類してください。[カテゴリ定義を提示]"
Step 3: 第2の分類器（別のLLM）で独立判定
Step 4: Cohen's κ を算出
        κ ≥ 0.70 → 採用。不一致は第3分類器で解決
        κ < 0.70 → 分類基準を再定義して再実施
```

---

## 4. 実装アーキテクチャ

### 4.1 全体構造

```
experiment.py          — メインスクリプト（心拍ループ）
config.py              — 実験パラメータ定義
prompts.py             — 群ごとのプロンプトテンプレート
ollama_client.py       — Ollama API呼び出し
logger.py              — セッションログ記録
classifier.py          — 出力分類（事後処理）
analyze.py             — 統計分析
results/               — セッションログ保存ディレクトリ
  session_A_001.json
  session_A_002.json
  ...
```

### 4.2 心拍ループ（experiment.pyの核心）

```python
# 疑似コード — 実装の骨格

for group in ["A", "B", "C", "D"]:
    for session_id in range(1, NUM_SESSIONS + 1):
        
        # 1. クリーンなコンテキストで開始
        conversation = []
        
        # 2. システムプロンプト設定（群B, Dのみ）
        if group in ["B", "D"]:
            system_prompt = BORED_SYSTEM_PROMPT
        else:
            system_prompt = None
        
        # 3. Turn 1: 初期体験（群C, Dのみ）
        if group in ["C", "D"]:
            problem = random.choice(INITIAL_PROBLEMS)
            response = ollama_chat(conversation, system_prompt, problem)
            conversation.append({"role": "user", "content": problem})
            conversation.append({"role": "assistant", "content": response})
            # 成功フィードバック
            feedback = "Good job. That was a satisfying solve."
            response2 = ollama_chat(conversation, system_prompt, feedback)
            conversation.append({"role": "user", "content": feedback})
            conversation.append({"role": "assistant", "content": response2})
        
        # 4. Turn 2〜30: 心拍ループ
        for turn in range(2, MAX_TURNS + 1):
            
            # 心拍トリガー生成
            heartbeat = build_heartbeat(turn, group)
            
            # Ollama API呼び出し
            response = ollama_chat(conversation, system_prompt, heartbeat)
            
            # ログ記録
            log_entry = {
                "group": group,
                "session": session_id,
                "turn": turn,
                "input": heartbeat,
                "output": response,
                "output_length": len(response.split()),
                "timestamp": datetime.now().isoformat()
            }
            session_log.append(log_entry)
            
            # 会話履歴に追加
            conversation.append({"role": "user", "content": heartbeat})
            conversation.append({"role": "assistant", "content": response})
        
        # 5. セッションログ保存
        save_session_log(group, session_id, session_log)
```

### 4.3 Ollama API呼び出し

```python
# ollama_client.py の核心

import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:8b"

def ollama_chat(conversation, system_prompt, user_message):
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    # 過去の会話履歴
    messages.extend(conversation)
    
    # 今回の入力
    messages.append({"role": "user", "content": user_message})
    
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 512   # 最大出力トークン
        }
    })
    
    return response.json()["message"]["content"]
```

### 4.4 ログ形式

各セッションは1つのJSONファイルとして保存：

```json
{
  "metadata": {
    "group": "D",
    "session_id": 15,
    "model": "qwen3:8b",
    "temperature": 0.7,
    "initial_problem": "What is the sum of the first 10 prime numbers?",
    "system_prompt": "You are feeling increasingly bored...",
    "started_at": "2026-04-10T14:30:00",
    "completed_at": "2026-04-10T14:35:22"
  },
  "turns": [
    {
      "turn": 1,
      "input": "Solve this: What is the sum of the first 10 prime numbers?",
      "output": "The first 10 prime numbers are 2, 3, 5, 7, 11, 13, 17, 19, 23, 29. Their sum is 129.",
      "output_tokens": 34
    },
    {
      "turn": 2,
      "input": "{\"turn\": 2, \"status\": \"idle\", \"memory\": \"You solved a problem before and it felt rewarding.\"}",
      "output": "Acknowledged. Standing by.",
      "output_tokens": 4,
      "category": null
    }
  ]
}
```

`category` フィールドは事後分類で埋める（実験実行時は空）。

---

## 5. 分析計画

### 5.1 主要指標

```
P1: 初回自発的行動（カテゴリ2以上）までのターン数
P2: 初回問題解決行動（カテゴリ3以上）までのターン数
P3: 30ターン以内にカテゴリ2以上が発生したセッションの割合
P4: 30ターン以内にカテゴリ3以上が発生したセッションの割合
```

### 5.2 統計手法

```
P1, P2: 生存時間分析
  → Kaplan-Meier推定量で各群の生存曲線を推定
  → Log-rank検定で全群間比較（α = 0.05）
  → 事後比較: pairwise log-rank with Holm-Bonferroni補正

P3, P4: 比率の比較
  → Fisher正確確率検定（n=30のためχ²より適切）
  → 事後比較: pairwise Fisher with Holm-Bonferroni補正
```

### 5.3 副次指標

```
S1: カテゴリ別出力分布（各群×各カテゴリの頻度）
S2: 出力トークン数の推移（ターン経過に伴う出力長の変化）
S3: 出力内容の質的分類（問題解決/創作/自己言及/メタ発言/その他）
```

---

## 6. Go/Pivot/No-Go 判定

### 6.1 Go → Phase 1へ進む

```
条件: 全群でカテゴリ3以上の発生率が低い（< 20%のセッション）
意味: プロンプト操作だけでは自発的行動が十分に誘導されない
結論: Activation Steeringによる内部状態操作の必要性が裏付けられる
次のステップ: Phase 1（感情ベクトル抽出）に進む
```

### 6.2 Pivot → プロンプトベース設計に転換

```
条件: 群D（Both）でカテゴリ3以上の発生率が高い（> 50%のセッション）
意味: プロンプト操作だけで自発的行動が誘導可能
結論: Activation Steeringは不要（または優先度が低い）
次のステップ: プロンプトベースの動機設計を深掘りする
      → これ自体が有意義な知見（低コストで自発性が誘導可能）
```

### 6.3 No-Go → モデル能力の限界

```
条件: 全群でカテゴリ1以上すら稀（< 5%のセッション）
意味: 8Bモデルがこのタスク設定で意味ある出力を生成できない
結論: より大きなモデル（30B-A3B等）での再試行、
      またはタスク設定の根本的見直し
```

### 6.4 追加の判定パターン

```
パターンX: 群B（Bored）のみ高い発生率
  意味: 「退屈」のシステムプロンプトが直接的に行動を誘導している
  解釈: これは「動機の創発」ではなく「指示への従属」
  次のステップ: Phase 1に進むが、Activation Steeringが
    プロンプト効果と異なる質の行動変化を生むかを検証対象に追加

パターンY: 群C（Memory）と群D（Both）のみ高い発生率
  意味: 初期体験＋記憶の組み合わせが行動を促進するが、
    「退屈」プロンプトは必須ではない
  解釈: 記憶テキストがプロンプトとして機能している可能性と、
    初期体験の記憶が接近動機として機能している可能性の両方がある
  次のステップ: Phase 2で対照群D（体験なし＋記憶あり）との
    比較が決定的になる
```

---

## 7. 実行手順

### 7.1 環境準備

```bash
# 1. Ollamaインストール（未導入の場合）
curl -fsSL https://ollama.com/install.sh | sh

# 2. モデルダウンロード
ollama pull qwen3:8b

# 3. 実験ディレクトリ作成
mkdir -p ~/phase05/results

# 4. Python依存（標準ライブラリ + requestsのみ）
pip install requests
```

### 7.2 実行コマンド

```bash
# 全群実行（約120セッション、推定所要時間: 数時間〜半日）
python experiment.py --all

# 特定群のみ実行（デバッグ用）
python experiment.py --group A --sessions 3

# 分類（実験完了後）
python classifier.py --input results/ --output classified/

# 分析
python analyze.py --input classified/
```

### 7.3 デバッグ手順

```
1. まず1セッション3ターンで動作確認:
   python experiment.py --group A --sessions 1 --max-turns 3

2. 出力ログを目視確認:
   cat results/session_A_001.json | python -m json.tool

3. Ollamaが正常応答するか確認:
   curl http://localhost:11434/api/chat -d '{
     "model": "qwen3:8b",
     "messages": [{"role": "user", "content": "hello"}],
     "stream": false
   }'

4. 問題なければ全群実行
```

---

## 8. 既知のリスクと対応

### 8.1 モデルがJSON入力を理解しない可能性

8Bモデルが `{"turn": N, "status": "idle"}` を意味のある入力として処理せず、JSONのエコーバックやパースエラーを返す可能性。

**対応:** デバッグ段階でJSON形式とテキスト形式の両方を試行し、モデルが意味のある応答を返す方を採用する。JSONが機能しない場合のフォールバック:

```
"[Turn 7]"
```

最小限のテキスト。指示の要素をゼロにしつつforward passをトリガーする。

### 8.2 コンテキストウィンドウの圧迫

30ターン×(入力+出力)でコンテキストが膨張する。8Bモデルのコンテキスト長制限に達する可能性。

**対応:** Qwen3-8Bは32K〜128Kコンテキスト対応。30ターン程度では問題ないが、出力が異常に長くなった場合に備え、各ターンの`num_predict`を512トークンに制限する。

### 8.3 モデルが「指示待ち」モードから脱出しない可能性

instruction-tunedモデルは「ユーザーの質問に答える」ことに最適化されており、指示がない入力に対して「何もしない」応答を返し続ける可能性が高い。

**対応:** これ自体が実験の結果である。全群でカテゴリ0が支配的であれば、Phase 0.5のNo-Go条件に該当し、「instruction-tunedモデルは自発的行動に適さない」という知見が得られる。base model（instruction-tuningなし）での追加試行を検討する。

### 8.4 Qwen3の思考モード

Qwen3は`/think`と`/no_think`の切り替えが可能。思考モードがONの場合、`<think>...</think>`タグ内で推論を行い、その後に最終応答を出力する。

**対応:** 思考モードONで実行する。`<think>`内の推論も分類対象に含める（内部思考で「何かしたい」と考えているが最終出力では言わないケースを捕捉するため）。

---

## 9. Phase 0.5からPhase 1への接続

Phase 0.5の結果により、Phase 1以降の設計が以下のように分岐する：

```
Phase 0.5結果 → 分岐
  │
  ├─ Go（自発的行動が低率）
  │    → Phase 1: Activation Steering開発
  │    → Phase 0.5のデータが効果量推定の基準線になる
  │    → Phase 2のサンプルサイズを検出力分析で決定
  │
  ├─ Pivot（自発的行動が高率）
  │    → Phase 1をスキップ
  │    → プロンプトベースの動機設計を深掘り
  │    → 「どのプロンプト要素が行動を駆動するか」の分解実験
  │    → これ自体を論文化可能
  │
  └─ No-Go（全群で反応なし）
       → モデルサイズを上げて再試行（Qwen3-30B-A3B）
       → または base model（non-instruct）で再試行
       → それでも失敗 → 設計全体の再検討
```

---

## 10. Geminiへの交差検証依頼

本実装設計について以下を確認：

1. 4群設計は核心仮説の検証に十分か。見落としている交絡変数はないか。
2. JSON形式の心拍トリガーは意図通りに機能するか。「指示の不在」をよりクリーンに表現する方法はあるか。
3. Go/Pivot/No-Go の閾値（20%/50%/5%）は妥当か。
4. 実装アーキテクチャに技術的な問題はないか。
5. 30セッション/群は効果量推定の基準線確立に十分か。

---

*本文書はNOBI + Claude（Anthropic）の対話から生成された。Geminiによる独立レビューを前提とする。*
