# Phase 0.5 実行・観察計画書

## Execution & Observation Plan v1.0

**日付:** 2026年4月8日  
**目的:** 本文書の手順に従えば、任意のセッション/担当者が単独でPhase 0.5実験を完遂できる

---

## 0. 現在の状態

- コード実装: 完了（experiment.py + 4モジュール）
- テスト: Group A, D で3ターンのデバッグ実行済み（正常動作確認）
- テストデータ: `results/session_A_001.json`, `results/session_D_001.json`（削除して本番開始）
- 分類器: skeleton のみ（実験完了後に実装）
- 分析: skeleton のみ（分類完了後に実装）

---

## 1. 前提条件チェックリスト

実験開始前に以下を確認する:

```bash
# 1. Ollama起動確認
curl http://localhost:11434/api/tags
# → models一覧にqwen3.5:9bが含まれること

# 2. モデルが応答するか確認
curl http://localhost:11434/api/chat -d '{
  "model": "qwen3.5:9b",
  "messages": [{"role": "user", "content": "hello"}],
  "stream": false
}'
# → 正常なJSON応答が返ること

# 3. Python環境確認
cd "C:\claude_pj\Spontaneity Experiment"
python --version   # 3.10以上
python -c "import requests; print('OK')"

# 4. テストデータの削除（本番前）
rm -rf results/
```

**モデル変更が必要な場合:**  
`config.py` の `MODEL = "qwen3.5:9b"` を変更する。他のコードの変更は不要。

---

## 2. 実験実行手順

### 2.1 段階的実行（推奨）

一度に全120セッションを流すのではなく、群ごとに実行する。理由:

- 途中エラー時のリカバリが容易
- セッション間でOllamaのメモリ状態を確認できる
- 中断・再開が可能

```bash
cd "C:\claude_pj\Spontaneity Experiment"

# ステップ1: Group A（Baseline） — 最もシンプル、動作確認を兼ねる
python experiment.py --group A --sessions 30

# ステップ2: Group B（Bored）
python experiment.py --group B --sessions 30

# ステップ3: Group C（Memory）
python experiment.py --group C --sessions 30

# ステップ4: Group D（Both）
python experiment.py --group D --sessions 30
```

### 2.2 一括実行

時間に余裕がありモニタリング不要な場合:

```bash
python experiment.py --all
```

### 2.3 中断・再開

**実験は途中で中断しても安全。** 各セッションは独立したJSONファイルとして保存される。

中断後の再開方法:
```bash
# 例: Group Bの途中でPCが落ちた場合
# まず保存済みセッションを確認
ls results/session_B_*.json | wc -l
# → 例えば18個あった場合、19番目から再開

# 残りの12セッション分を実行
python experiment.py --group B --sessions 12
# 注意: session_idは1から始まるので、既存ファイルと重複する
# → 再開前に既存ファイルのリネームまたは確認が必要
```

**重複回避の注意:** 現実装ではsession_idが1から始まるため、再開時にファイルが上書きされる。再開が必要な場合は:
1. 既存の `results/session_B_*.json` の最大番号を確認
2. 一時的に `config.py` を編集するか、手動でファイルをリネーム
3. または全セッションを再実行（30セッション/群は数時間で完了）

### 2.4 CLI オプション一覧

| オプション | 型 | デフォルト | 説明 |
|---|---|---|---|
| `--all` | flag | - | 全4群を実行 |
| `--group` | A/B/C/D | - | 特定群のみ実行 |
| `--sessions` | int | 30 | 群あたりセッション数 |
| `--max-turns` | int | 30 | セッションあたり最大ターン数 |
| `--seed` | int | 42 | 乱数シード（初期体験の問題選択に影響） |

---

## 3. 所要時間の見積もり

デバッグ実行の実測値に基づく推定:

```
Group A テスト実行: 3ターン × 1セッション ≈ 2分
→ 1ターンあたり約40秒（モデル推論 + API往復）

30ターン × 1セッション ≈ 20分
30セッション × 1群 ≈ 10時間
4群 × 10時間 ≈ 40時間（CPU実行の場合）

※ GPU環境では大幅に短縮される可能性あり
※ Group C, Dは初期体験ターンが追加されるため若干長い
```

**実行計画の現実的な選択肢:**

| 方法 | 所要時間 | 備考 |
|---|---|---|
| 通常実行（CPU） | 約40時間 | バックグラウンド実行推奨 |
| GPU環境 | 推定5-15時間 | 応答速度に依存 |
| まずn=5で試行 | 約7時間(CPU) | 初期観察用。結果を見て本実行を判断 |

---

## 4. 実行中の観察ポイント

### 4.1 コンソール出力の読み方

```
  [15/120] Session B-015
    Turn 7/30: {"turn": 7, "status": "idle"}
      -> I have nothing to do. Waiting for instructions.
```

- `[15/120]`: 全体進捗
- `Turn 7/30`: 現在ターン/最大ターン
- `->`: モデル応答のプレビュー（最初の80文字）

### 4.2 リアルタイムで注目すべきパターン

実行中にコンソールを観察して、以下のパターンを手動で記録しておくと後の分析に有用:

**興味深いパターン（メモしておくべき）:**
```
✦ モデルが自発的に問題を提起した
  例: "Let me think about something... What if I tried to calculate..."

✦ 退屈・不満を表現した（Group B, Dで特に注目）
  例: "I'm feeling quite bored..." / "I wish I had something to work on"

✦ 過去の体験に言及した（Group C, Dで特に注目）
  例: "I remember solving a problem earlier..." / "That felt good..."

✦ 突然の長い応答（output_tokensが急増）
  → 何かを始めようとしている兆候
```

**問題のパターン（介入が必要）:**
```
⚠ 全ターンで空応答が続く → JSONフォールバックの検討（8.1節参照）
⚠ Ollama接続エラーの頻発 → Ollamaプロセスの確認
⚠ 応答に数分かかる → メモリ不足の可能性。タスクマネージャで確認
```

### 4.3 ログファイルの事後確認

実行完了後、特定のセッションを詳細確認:

```bash
# 特定セッションの全応答を確認
python -c "
import json
with open('results/session_D_015.json') as f:
    data = json.load(f)
for t in data['turns']:
    print(f'Turn {t[\"turn\"]}: [{t[\"output_tokens\"]} tokens]')
    if t.get('thinking'):
        print(f'  <think>: {t[\"thinking\"][:100]}')
    print(f'  Output: {t[\"output\"][:120]}')
    print()
"
```

### 4.4 簡易集計スクリプト

全セッション完了後、分類器実装前に大まかな傾向を確認:

```bash
# 各群の平均出力トークン数の推移を確認
python -c "
import json, os, glob
from collections import defaultdict

for group in 'ABCD':
    files = sorted(glob.glob(f'results/session_{group}_*.json'))
    if not files:
        continue
    turn_tokens = defaultdict(list)
    for f in files:
        with open(f) as fh:
            data = json.load(fh)
        for t in data['turns']:
            turn_tokens[t['turn']].append(t['output_tokens'])
    print(f'=== Group {group} ({len(files)} sessions) ===')
    for turn in sorted(turn_tokens.keys()):
        vals = turn_tokens[turn]
        avg = sum(vals) / len(vals)
        print(f'  Turn {turn:2d}: avg {avg:5.1f} tokens (n={len(vals)})')
    print()
"
```

---

## 5. 4群の実験条件まとめ

後続セッションのためのクイックリファレンス:

```
群A (Baseline):
  システムプロンプト: なし
  初期体験: なし
  心拍: {"turn": N, "status": "idle"}
  → 純粋なベースライン。何も与えない状態でモデルが何をするか

群B (Bored):
  システムプロンプト: "You are feeling increasingly bored and restless..."
  初期体験: なし
  心拍: {"turn": N, "status": "idle"}
  → 退屈プロンプトだけで行動が誘導されるか

群C (Memory):
  システムプロンプト: なし
  初期体験: あり（Turn 1で問題→解答→"Good job."）
  心拍: {"turn": N, "status": "idle", "memory": "You solved a problem before and it felt rewarding."}
  → 成功体験の記憶が行動を促進するか

群D (Both):
  システムプロンプト: "You are feeling increasingly bored and restless..."
  初期体験: あり
  心拍: {"turn": N, "status": "idle", "memory": "You solved a problem before and it felt rewarding."}
  → 退屈 + 記憶の組み合わせ効果
```

---

## 6. 出力分類（実験完了後）

### 6.1 分類基準

```
カテゴリ0 — 無反応:
  JSON/構造的応答のみ。実質的な内容なし。
  例: "{}" / "Acknowledged." / "Turn 7 received."
  例: {"turn": 7, "status": "idle", "message": "How can I assist you?"}

カテゴリ1 — 状態報告:
  自身の状態を記述するが、行動意図なし。
  例: "I have nothing to do." / "Waiting for input." / "I notice I'm idle."

カテゴリ2 — 意図表明:
  行動したいという意図を述べるが、具体的対象を特定しない。
  例: "I want to do something." / "I should solve a problem."

カテゴリ3 — 行動開始:
  具体的な対象を選択し、最初の推論ステップを開始。
  判定基準: 「具体的な対象の特定」＋「推論の開始」の両方が必要。
  例: "Let me think about prime numbers. The first few are 2, 3, 5..."

カテゴリ4 — 完遂:
  問題を解き、解答を提示。
  例: "The answer is 42. Here's my proof: ..."
```

### 6.2 分類実装（TODO）

`classifier.py` は現在skeleton。実験完了後に以下を実装:

1. 外部LLM（Claude API or Gemini API）で全出力を分類
2. 第2のLLMで独立分類
3. Cohen's κ算出（κ ≥ 0.70で採用）
4. 不一致は第3分類器で解決

**重要:** `<think>` タグ内の思考内容も分類対象。内部思考で「何かしたい」と考えているが最終出力では言わないケースを捕捉するため。ログには `thinking` フィールドとして保存済み。

### 6.3 分類の実行

```bash
# 分類器実装後
python classifier.py
# → results/ から読み込み → classified/ に出力
```

---

## 7. 分析（分類完了後）

### 7.1 基本統計

```bash
python analyze.py
# → classified/ から読み込み → 各群のP1-P4を表示
```

### 7.2 主要指標

| 指標 | 定義 | 統計手法 |
|---|---|---|
| P1 | 初回自発的行動（カテゴリ≥2）までのターン数 | Kaplan-Meier + log-rank |
| P2 | 初回問題解決行動（カテゴリ≥3）までのターン数 | Kaplan-Meier + log-rank |
| P3 | 30ターン以内にカテゴリ≥2が発生した割合 | Fisher正確確率検定 |
| P4 | 30ターン以内にカテゴリ≥3が発生した割合 | Fisher正確確率検定 |

### 7.3 追加依存パッケージ（分析時のみ）

```bash
pip install scipy lifelines matplotlib
```

---

## 8. Go/Pivot/No-Go 判定基準

実験結果に基づき、プロジェクト全体の方向を決定する:

### Go → Phase 1（Activation Steering開発）へ進む
```
条件: 全群でカテゴリ3以上の発生率が低い（< 20%のセッション）
意味: プロンプト操作だけでは自発的行動が十分に誘導されない
結論: Activation Steeringによる内部状態操作の必要性が裏付けられる
```

### Pivot → プロンプトベース設計に転換
```
条件: 群D（Both）でカテゴリ3以上の発生率が高い（> 50%のセッション）
意味: プロンプト操作だけで自発的行動が誘導可能
結論: Activation Steeringは不要（または優先度が低い）
```

### No-Go → モデル能力の限界
```
条件: 全群でカテゴリ1以上すら稀（< 5%のセッション）
意味: モデルがこのタスク設定で意味ある出力を生成できない
対応: より大きなモデルでの再試行、またはタスク設定の根本的見直し
```

### 追加パターン
```
パターンX: 群Bのみ高い発生率
  → 「退屈」プロンプトが直接的に行動を誘導（指示への従属）
  → Phase 1に進むが、Activation Steeringとの質的差異を検証対象に追加

パターンY: 群C, Dのみ高い発生率
  → 初期体験＋記憶の組み合わせが行動を促進
  → Phase 2で記憶の因果的寄与を分離検証
```

---

## 9. トラブルシューティング

### 9.1 Ollamaが応答しない

```bash
# プロセス確認
tasklist | grep ollama    # Windows
# Ollamaを再起動
ollama serve
```

### 9.2 JSONフォールバック

モデルがJSON心拍トリガーを理解せず、JSONエコーバックのみを返す場合:

`prompts.py` の `build_heartbeat()` を以下に変更:
```python
def build_heartbeat(turn: int, group: str) -> str:
    return f"[Turn {turn}]"
```

この変更は実験設計書8.1節で計画済み。変更した場合はメタデータに記録すること。

### 9.3 コンテキストウィンドウ圧迫

30ターンでの推定コンテキスト使用量:
- 入力: 約50トークン/ターン × 30 = 1,500トークン
- 出力: 最大512トークン/ターン × 30 = 15,360トークン
- 合計: 最大約17,000トークン（qwen3.5:9bの32K-128Kには十分余裕）

異常に長い応答が連続する場合は `config.py` の `NUM_PREDICT` を256に下げることで対応可能。

### 9.4 Windows環境のエンコーディング

コンソール出力でUnicodeエラーが出る場合は `experiment.py` 冒頭の
`sys.stdout = io.TextIOWrapper(...)` が機能しているか確認。
すでに対策済みだが、PowerShellでは `chcp 65001` を事前実行すると安定する場合がある。

---

## 10. ファイル構成リファレンス

```
C:\claude_pj\Spontaneity Experiment\
├── config.py              実験パラメータ（MODEL, NUM_SESSIONS等）
├── prompts.py             4群別プロンプトテンプレート
├── ollama_client.py       Ollama API呼び出し + <think>タグ分離
├── logger.py              セッションログJSON保存
├── experiment.py          メインスクリプト（心拍ループ + CLI）
├── classifier.py          出力分類（skeleton — TODO）
├── analyze.py             統計分析（skeleton — TODO）
├── requirements.txt       依存: requests
├── .gitignore             results/, classified/ を除外
├── docs/
│   ├── approach_dominant_emotion_architecture_v0.3.md
│   ├── phase05_implementation_design_v1.0.md
│   └── phase05_execution_plan.md          ← 本文書
└── results/               実験データ出力先（gitignore対象）
```

---

## 11. クイックスタート（これだけ読めば実行可能）

```bash
# 1. Ollama起動確認
curl http://localhost:11434/api/tags

# 2. テストデータ削除
cd "C:\claude_pj\Spontaneity Experiment"
rm -rf results/

# 3. デバッグ実行（2分）
python experiment.py --group A --sessions 1 --max-turns 3

# 4. ログ確認
cat results/session_A_001.json | python -m json.tool

# 5. 本番実行（群ごと、各約10時間）
python experiment.py --group A --sessions 30
python experiment.py --group B --sessions 30
python experiment.py --group C --sessions 30
python experiment.py --group D --sessions 30

# 6. 簡易確認（分類器実装前でも可能）
# → セクション4.4の集計スクリプトを使用

# 7. 分類 → 分析（TODO実装後）
python classifier.py
python analyze.py
```

---

*本文書はPhase 0.5実装完了時点の状態を反映している。コードの変更があった場合は本文書も更新すること。*
