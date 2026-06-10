# MarkItDown と uv のメモ

変換コマンド、依存関係の選択、品質上の注意点が不明な場合にだけ、この参照ファイルを読む。

## スキル作成時に確認した事実

- Microsoft MarkItDownは、LLMやテキスト分析パイプライン向けにファイルをMarkdownへ変換するPythonパッケージ兼CLIである。
- MarkItDownはPDF変換をサポートし、抽出可能な範囲で見出し、リスト、リンク、表などの構造を保持する。
- MarkItDownの出力はLLM処理やテキスト処理向けであり、人間向けの高忠実度な文書再現を目的にしていない。
- MarkItDownは、現在のプロセス権限でI/Oを実行する。信頼できない入力は検査し、用途に合う狭い変換関数を優先する。
- MarkItDownのREADMEはCLI使用例として`markitdown path-to-file.pdf -o document.md`を示している。
- MarkItDownのREADMEはPython API使用例として`from markitdown import MarkItDown; result = md.convert("test.xlsx"); result.text_content`を示している。
- MarkItDownのパッケージコードは、ローカルファイル用に`MarkItDown.convert_local(path)`を提供している。
- uvは、インライン依存関係メタデータ付きの単一Pythonスクリプトを`uv run script.py`で実行できる。
- uvはプロジェクトまたはタスク単位の仮想環境を作れる。このスキルでは、呼び出し元プロジェクトの依存関係を恒久的に変更しないためにuvのスクリプト実行を使う。

## 推奨コマンド

`--output`を省略し、PDFと同じディレクトリに同じベース名のMarkdownを書き出す。

```bash
uv run scripts/convert_pdf.py path/to/input.pdf
```

## MarkItDown直接実行のフォールバック

同梱スクリプトが使えない場合だけ使う。出力先はPDFと同じディレクトリに保つ。

```bash
uvx --from 'markitdown[pdf]' markitdown path/to/input.pdf -o path/to/input.md
```

## 品質上の注意点

- テキストレイヤーを持つPDFは、スキャンPDFより変換品質が高くなりやすい。
- スキャンPDFや画像のみのPDFは、OCRなしではほとんど、またはまったくテキストを抽出できない場合がある。
- 表、数式、脚注、ヘッダー、複数カラムレイアウトは、元PDFとのスポットチェックが必要になることがある。
- Markdown変換はLLM入力の負荷を下げるが、意味内容の完全性は保証しない。
