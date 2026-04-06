---
name: coherence-agent-text
description: "草案の流れ・接続・冗長・論理飛躍を検査し、Change/Insert/Delete/Reorder 形式で修正案を出す。He & Martens (2026) の Coherence Agent に相当。接続詞、段落構成、読みやすさ、文章のつながり、違和感の指摘と依頼されたら使う。事実や数値の訂正は扱わない（それは faithful 系）。"
---

# Coherence Agent — Text

## 目的

**言語的・修辞的**な一貫性を高める。論文では coherence を fluency + grammar + logical flow の傘概念として扱う。

## 手順

1. 草案を読み、**唐突な転換**、**不適切な接続詞**、**重複**、**主題のブレ**を探す。
2. 修正案は次の4テンプレのいずれかに限定する（論文 Sec.2.1）:
   - `Change ___ to ___`
   - `Insert ___ before ___`
   - `Delete ___`
   - `Reorder ___ after ___`
3. 各提案の下に `Justification:` を付ける。
4. 問題なしなら `no coherence issues` と理由を一行。

## Why

読みやすさは正しさだけでは足りない。ただし論文でも、Coherence 最適化は **faithfulness を損なうことがある**ため、提案は Narrator が拒否してよい。

## 参照

境界例は `references/faithfulness-coherence-tradeoff.md`。
