---
name: faithful-evaluator-text
description: "草案がソース文章に忠実かを、構造化抽出＋照合で検査する。数値・固有名・因果・極性の誤りを列挙する。He & Martens (2026) の Faithful Evaluator を一般テキスト向けに適用。事実確認、根拠チェック、ハルシネーション検出、ソースとの整合性、誤情報リスクレビューと依頼されたら必ず使う。SHAPや表形式の説明だけのタスクでは使わない。"
---

# Faithful Evaluator — Text

## 目的

草案に現れる**検証可能な主張**を抽出し、`source_text` と突き合わせて誤りを列挙する。論文の rank / sign / value に代わる軸は次のとおり。

| 軸 | 意味 |
|----|------|
| coverage | ソース上の主要点が過度に欠落していないか |
| entity / number | 固有名・数値・日付の一致 |
| polarity | 肯定・否定・評価の向きの一致 |
| causal | 因果の向き・条件の一致 |
| unsupported | ソースにない断定の混入 |

## 手順

1. 草案を**主張単位**に分解（1〜3文ずつラベル）。
2. 各主張についてソース中の根拠の有無を判定: `supported | partial | unsupported | contradiction`。
3. 誤りを固定フォーマットで列挙（エージェント定義の文面に合わせる）。
4. 誤りゼロならスコープ内で fully faithful と宣言。

## Why

自動ループで改善するには、**人間が読む前に機械的に比較できる中間表現**が必要だからである（論文では SHAP 行との比較）。

## 参照

抽出の粒度例・境界ケースは `references/evaluation-rubric.md`。
