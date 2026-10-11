# 説明設計: 問い・根拠・視覚表現

## 図を必要とする問い

最初に「誰が、どの前提知識で、何を理解できていないか」を書く。理解のつまずきは「難しい」ではなく、「分岐条件が分からない」「層の内外を混同する」「二つの処理の待ち方の違いが分からない」のように特定する。

図が加える説明を一文にする。順序・包含・比較軸・状態変化を視覚的に追えるなら図にする。単純な項目列挙で追加する説明がなければ文章・表を使う。複数図に分ける場合も一図一問を保つ。

## ブリーフの追加項目

新規制作では、スキル同梱の `assets/diagram-brief-template.json` の既存項目に次の `explanation` を記入する。既存ブリーフの構造は維持し、検証器はこのオブジェクトがない旧形式も受け付ける。

```json
{
  "explanation": {
    "reader_question": "キャッシュがある場合とない場合で取得経路はどう変わるか？",
    "understanding_gap": "キャッシュミス時にどこから取得するかが分からない",
    "visual_strategy": "ヒットとミスの条件を分け、各取得経路を追えるようにする",
    "output_format": "mermaid",
    "source_basis": [
      {"id": "s1", "text": "入力の記述: ヒットならキャッシュ、ミスなら保存元から取得する"}
    ],
    "claim_visual_map": [
      {"claim": "ヒット時はキャッシュから取得する", "source_ids": ["s1"], "element_ids": ["e1", "e2"]},
      {"claim": "ミス時は保存元から取得する", "source_ids": ["s1"], "element_ids": ["e1", "e3"]}
    ]
  }
}
```

これは追加項目だけの例であり、全体ブリーフの `elements` に `e1`（取得要求）、`e2`（キャッシュ）、`e3`（保存元）を定義し、対応する `relationships` に取得経路と分岐条件を記録する。`output_format` は `mermaid` または `svg` とする。

- `reader_question`: 図を見た後に読者が答えられる一つの問い。
- `understanding_gap`: 現在の理解で欠けている関係・区別・変化。
- `visual_strategy`: 配置・線・グループなどが、そのつまずきをどう解消するか。
- `source_basis`: 根拠を識別する非空の `id` と `text`。入力の段落や外部ソースのURL・該当箇所を追跡できるように書く。
- `claim_visual_map`: 主要な `claim` を、存在する `source_ids` と `element_ids` へ対応づける。線や注釈も対象要素と関係の記述を通じて照合する。

## ソース忠実性の確認

1. 主張ごとに、入力が実際に支持する記述を探す。言い換えと追加した解釈を区別する。
2. 時間順を因果に、近接を依存に、レイヤーを優劣に変えない。矢印には「取得」「次の状態」など意味を明示する。
3. 条件・例外・適用範囲を省略すると誤読するなら注釈を加える。根拠不明の関係は `open_questions` に残し、断定しない。
4. 主要な要素・線・注釈をブリーフに照合する。JSONの参照が有効でも、その主張が正しいとは限らない。

比喩を使う場合は「どの概念が何に対応するか」と「どこまで対応するか」を説明する。直接の関係図で伝わるなら比喩を足さない。

## anatomyから参考にした原則

参照コミット: `dbf697a527bbf7d358668e1557cb1e35ff725d46`。原則を一般の静的な説明図へ応用し、手順は独自に記述している。

| 参考にした考え方 | このスキルへの適用 | 出典 |
|---|---|---|
| 挙動を整理し、概念と機構・部品を対応づけてから描く | 理解の問いから根拠と図の要素を対応づける | [SKILL.md:52–64](https://github.com/wheresryan22/anatomy/blob/dbf697a527bbf7d358668e1557cb1e35ff725d46/SKILL.md#L52-L64) |
| SVGなどの成果物を作る | 図解仕様に加えて実際の図ファイルを納品する | [SKILL.md:98–101](https://github.com/wheresryan22/anatomy/blob/dbf697a527bbf7d358668e1557cb1e35ff725d46/SKILL.md#L98-L101) |
| 部品と説明の対応を保つ | ラベル・線・注釈を同じブリーフと照合する | [walkthrough.md:5–21](https://github.com/wheresryan22/anatomy/blob/dbf697a527bbf7d358668e1557cb1e35ff725d46/references/walkthrough.md#L5-L21) |
| 表示結果を検査する | 意味照合と実描画の確認を別々に記録する | [SKILL.md:67–73](https://github.com/wheresryan22/anatomy/blob/dbf697a527bbf7d358668e1557cb1e35ff725d46/SKILL.md#L67-L73)、[verify.md](https://github.com/wheresryan22/anatomy/blob/dbf697a527bbf7d358668e1557cb1e35ff725d46/references/verify.md) |

等角投影、機械の比喩、3D、対話型の挙動や部品数は制作要件にしない。図の密度や装飾を増やすことを学習効果の証明とせず、読者の問いに答えられる構造を選ぶ。
