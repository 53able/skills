# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "markitdown[pdf]>=0.1.0",
# ]
# ///
"""MarkItDownでローカルPDFをMarkdownへ変換する。

このスクリプトはuvで実行する想定:
    uv run scripts/convert_pdf.py input.pdf
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Microsoft MarkItDownでローカルPDFをMarkdownへ変換する。"
    )
    parser.add_argument("pdf", help="ローカルPDFファイルのパス")
    parser.add_argument(
        "-o",
        "--output",
        help="出力Markdownパス。PDFと同じディレクトリ内に限る。省略時はPDFパスの拡張子を.mdに変える。", 
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="既存のMarkdown出力ファイルを上書きする。", 
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="ファイルではなく標準出力へMarkdownを書き出す。", 
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=20,
        help="抽出Markdownがこの文字数未満なら失敗にする。0で無効化する。", 
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pdf_path = Path(args.pdf).expanduser().resolve()

    if not pdf_path.exists():
        print(f"ERROR: PDFが見つかりません: {pdf_path}", file=sys.stderr)
        return 2
    if not pdf_path.is_file():
        print(f"ERROR: PDFパスがファイルではありません: {pdf_path}", file=sys.stderr)
        return 2
    if pdf_path.suffix.lower() != ".pdf":
        print(f"ERROR: .pdfファイルを指定してください: {pdf_path.name}", file=sys.stderr)
        return 2

    output_path = None
    if not args.stdout:
        output_path = Path(args.output).expanduser().resolve() if args.output else pdf_path.with_suffix(".md")
        if output_path.parent != pdf_path.parent:
            print(
                f"ERROR: 出力先はPDFと同じディレクトリにしてください: {pdf_path.parent}",
                file=sys.stderr,
            )
            return 3
        if output_path.exists() and not args.overwrite:
            print(
                f"ERROR: 出力ファイルが既に存在します: {output_path}。--overwriteを付けるか、--outputで別名を指定してください。",
                file=sys.stderr,
            )
            return 3
        output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from markitdown import MarkItDown

        converter = MarkItDown(enable_plugins=False)
        result = converter.convert_local(pdf_path)
        markdown = result.text_content or ""
    except Exception as exc:  # MarkItDownはコンバータ固有の例外を投げることがある。
        print(f"ERROR: MarkItDown変換に失敗しました: {pdf_path}: {exc}", file=sys.stderr)
        return 4

    if args.min_chars > 0 and len(markdown.strip()) < args.min_chars:
        print(
            f"ERROR: 抽出Markdownが{len(markdown.strip())}文字しかありません。PDFがスキャン画像、画像のみ、暗号化済み、または未対応の可能性があります。",
            file=sys.stderr,
        )
        return 5

    if args.stdout:
        sys.stdout.write(markdown)
        if markdown and not markdown.endswith("\n"):
            sys.stdout.write("\n")
        print(
            f"SUCCESS: {pdf_path}を標準出力へ変換しました（{len(markdown)}文字）。",
            file=sys.stderr,
        )
    else:
        assert output_path is not None
        output_path.write_text(markdown, encoding="utf-8")
        print(
            f"SUCCESS: {pdf_path} -> {output_path} に変換しました（{len(markdown)}文字）。"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
