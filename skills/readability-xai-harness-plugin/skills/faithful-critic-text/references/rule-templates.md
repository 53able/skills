# Faithful Critic — Rule テンプレート

以下をエラー型に埋め込む（論文の Faithful Critic (Rule) に近い）。

- **Rank / 強調の順序**: 「『{topic}』について述べる文を、『{topic2}』より前に移動してください。ソースでは {topic2} の方が主要です。」
- **Polarity**: 「『{snippet}』の評価を反転してください。ソースでは {polarity_evidence} です。」
- **Value**: 「『{snippet}』の数値を {correct_value} に修正してください（ソース: …）。」
- **Unsupported**: 「次の断定を削除するか、ソースの該当箇所を引用して弱めてください: …」
