---
name: pdf-markdown-local
description: ローカルPDFをLLM投入前にトークン効率のよいMarkdownへ変換する。Microsoft MarkItDownをuv管理のPython環境で実行する。PDFのトークン消費を抑えたい場合、PDF内容をMarkdownで確認したい場合、複数PDFを一括変換したい場合、再利用可能なローカル変換成果物を作る場合に使う。高忠実度の視覚再現、法務監査級の抽出、クラウドOCR、未ダウンロードまたは信頼未確認のURL入力には使わない。
---

# PDF Markdown ローカル変換

LLMにPDF本文を渡す前に、ローカルPDFをMarkdownへ変換する。変換にはMicrosoft MarkItDownを使い、依存関係はuvで隔離して、呼び出し元プロジェクトのPython環境を汚さない。

## 手順

1. 入力が信頼できるローカルPDFパスであることを確認する。
   - リモートURLを直接変換しない。
   - ファイルパスがない場合は、ローカルPDFパスの提示を依頼する。
   - 呼び出し元タスクが明示的に許可しない限り、PDFをクラウドサービスへアップロードしない。

2. コマンド構文、依存関係の選択、品質上の注意点が必要な場合だけ、`references/markitdown-uv-notes.md`を読む。

3. 出力Markdownパスを決める。
   - Markdownファイルは必ず元PDFと同じディレクトリに置く。
   - ファイル名は元PDFのベース名に`.md`を付ける。例: `paper.pdf` -> `paper.md`。
   - 元PDFファイルは変更しない。

4. このスキルディレクトリから、同梱コンバータをuvで実行する。標準では同一ディレクトリへ出力するため、`--output`は省略する。

   ```bash
   uv run scripts/convert_pdf.py path/to/input.pdf
   ```

   既存Markdownを意図的に置き換える場合だけ、`--overwrite`を付ける。

5. 同一ディレクトリに出力されたMarkdownが存在し、空でないことを確認する。

   ```bash
   test -s path/to/input.md && wc -c path/to/input.md
   ```

6. Markdownを根拠として使う前に、抽出品質をスポットチェックする。
   - Markdown冒頭とPDFのタイトルまたは1ページ目を比較する。
   - PDF中盤にあるはずの見出しまたは本文を検索する。
   - 結論、参考文献、付録など末尾側のセクションがある場合は検索する。
   - 表、数式、図、複数カラムの箇所は、直接確認していない限り`要手動確認`として扱う。

7. スポットチェックに通った場合、または制約を明記した場合だけ、下流のLLM読解にMarkdownを使う。

## 一括変換

PDFごとに1回ずつ変換し、エラーが出たら停止する。

```bash
for pdf in path/to/pdfs/*.pdf; do
  uv run scripts/convert_pdf.py "$pdf"
done
```

一括変換後は、`ls -lh path/to/pdfs/*.md`を実行し、代表ファイルをスポットチェックする。

## 報告

呼び出し元が監査可能な記録を必要とする場合は、`assets/conversion-report-template.md`を使う。元PDF、出力Markdownパス、実行コマンド、文字数、状態、スポットチェック結果を記録する。

## エラー処理

- `uv`が見つからない場合は、`blocked: uv is not installed or not on PATH`と報告する。インストール方法は、依頼された場合だけ`references/markitdown-uv-notes.md`の情報を示す。
- MarkItDown変換が失敗した場合は、PDFを保持し、stderrの正確なメッセージを報告する。抽出できていない内容を推測で作らない。
- 出力が空、または極端に短い場合は、変換結果を`要手動確認`とする。PDFがスキャン画像、暗号化済み、画像のみ、未対応形式である可能性は、可能性としてだけ述べる。
- PDFがスキャン画像または画像のみの場合、許可なくクラウドOCRへ切り替えない。明示的に利用可能なローカルOCR手順がある場合だけ使い、なければ確認を取る。
- 表、数式、図がタスクに重要な場合は、元PDFを確認するか、文書解析またはスクリーンショット系ツールを使う。Markdownだけを完全な証拠として扱わない。

## 検証チェックリスト

変換成果物を引き渡す前に、以下を確認する。

- [ ] `uv run scripts/convert_pdf.py`、または文書化されたuvフォールバックを使った。
- [ ] MarkdownファイルがPDFと同じディレクトリに存在する。
- [ ] Markdownファイルが空でなく、文字数を記録した。
- [ ] 少なくとも3つの内容スポットチェックを試みた。省略した確認がある場合は明記した。
- [ ] 既知の抽出制約を最終応答または報告書に記載した。
