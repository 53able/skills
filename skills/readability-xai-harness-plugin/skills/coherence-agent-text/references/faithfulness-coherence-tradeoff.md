# Faithfulness と Coherence のトレードオフ

arXiv:2603.20003 の結果では、Coherence Agent を入れた Coherent Design は **rank accuracy 悪化**や **不忠実なナラティブ残存**が報告されている（言語調整がモデルに誤った編集を誘発しうる）。

本ハーネスでの運用原則:

1. Coherence の提案が**事実を変える**場合は却下し、Faithful 系に回す。
2. 「読みやすさ」のための**段落入れ替え**は、因果順序をソースと矛盾させないか確認する。
