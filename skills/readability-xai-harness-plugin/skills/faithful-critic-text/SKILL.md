---
name: faithful-critic-text
description: "Faithful Evaluator の誤り報告を、ソースに基づく具体的な修正指示へ変換する。He & Martens (2026) の Faithful Critic（および Rule 版）に相当。レビューコメントを実装可能な指示に落とす、編集指示、修正案、どこを直すか明確に、と依頼されたら使う。スタイル好みだけのリライトには使わない。"
---

# Faithful Critic — Text

## 目的

Evaluator の検出結果を、Narrator が**一発で適用できる**命令に変換する。論文では誤りタイプごとに「段落の移動」「符号の反転」「値の訂正」など**方向づけ**を行う。

## 手順

1. `evaluator_report` の各エラーについて、ソースから**正しい情報**を引用（短く）。
2. 修正を **Delete / Replace / Reorder / Add qualification** に分類する。
3. 複数エラーがある場合、**忠実性への影響が大きい順**に並べる。
4. Rule モード: LLM を使わず、テンプレ文だけで済む場合は `references/rule-templates.md` を使う。

## Why

Evaluator だけでは「何が悪いか」までで止まる。Critic は**編集コストを下げる**ための差分指示を担う（論文 Fig.4）。

## 参照

- `references/rule-templates.md`
