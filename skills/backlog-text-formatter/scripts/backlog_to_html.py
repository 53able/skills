#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""backlog_to_html.py -- Backlog(Nulab)記法をHTMLへ決定的に変換するCLI。

依存は標準ライブラリのみだが、uvで依存関係を閉じ込めて実行する。

使い方:
    uv run scripts/backlog_to_html.py input.txt        # ファイルを変換して標準出力へ
    cat input.txt | uv run scripts/backlog_to_html.py -   # 標準入力から変換
    uv run scripts/backlog_to_html.py --test           # 内部の自己テストを実行

対応ルールの詳細は ../references/rules.md を参照。
"""
import argparse
import html
import re
import sys

ESCAPE_PERCENT = "\x00PCT\x00"
ESCAPE_BAR = "\x00BAR\x00"


def _escape_literals(text: str) -> str:
    # ルール19: \%\% と \|\| は記法として解釈させず、後で literal に戻す。
    text = text.replace("\\%\\%", ESCAPE_PERCENT)
    text = text.replace("\\|\\|", ESCAPE_BAR)
    return text


def _restore_literals(text: str) -> str:
    text = text.replace(ESCAPE_PERCENT, "%%")
    text = text.replace(ESCAPE_BAR, "||")
    return text


def _convert_rev(arg: str) -> str:
    # ルール13/14: ':' を含めばGitリビジョン(引数そのまま)、そうでなければSVN(r接頭辞)。
    if ":" in arg:
        return arg
    last = arg.split("/")[-1]
    if last.isdigit():
        return "r" + last
    return arg


def _convert_inline(text: str) -> str:
    """見出し・リスト・表・引用ブロックを除いた"素のテキスト"に対するインライン変換。"""

    # 画像・縮小画像 (ルール17/18)
    def _img(match, cls):
        url = match.group(1)
        alt = re.sub(r"\.[a-zA-Z0-9]+$", "", url.rsplit("/", 1)[-1])
        alt = re.sub(r"[_-]", " ", alt)  # 例: backlog_logo.svg -> "backlog logo"
        return f'<img src="{url}" class="{cls}" alt="{alt}">'

    text = re.sub(r"#image\(([^)]+)\)", lambda m: _img(m, "loom-external-image"), text)
    text = re.sub(r"#thumbnail\(([^)]+)\)", lambda m: _img(m, "loom-external-image-thumbnail"), text)

    # リビジョンリンク (ルール13/14)
    text = re.sub(
        r"#rev\(([^)]+)\)",
        lambda m: f'<button type="button" role="button" class="_trigger-text">{_convert_rev(m.group(1))}</button>',
        text,
    )

    # URL付きリンク [[表示名>URL]] / [[表示名:URL]] (ルール6)
    def _alias_link(m):
        label, url = m.group(1), m.group(2)
        return f'<a href="{url}" class="loom-link-another">{label}</a>'

    text = re.sub(r"\[\[([^\[\]>:]+)[>:](https?://[^\]]+)\]\]", _alias_link, text)

    # 課題キー / Wikiページリンク [[XXX]] (ルール1) -- URL形式に一致しなかった残り
    text = re.sub(
        r"\[\[([^\[\]]+)\]\]",
        r'<button type="button" role="button" class="_trigger-text">\1</button>',
        text,
    )

    # 生の課題キー (例: BLG-95) -- 既にボタン化された部分は _trigger-text クラス内なので
    # 単純な単語境界マッチで衝突する心配はほぼ無い。
    text = re.sub(
        r"(?<![\w>])([A-Z][A-Z0-9]+-\d+)(?![\w<])",
        r'<button type="button" role="button" class="_trigger-text">\1</button>',
        text,
    )

    # 生URL (ルール6) -- すでに href="..." / src="..." 属性値になっている箇所は
    # 二重変換しないよう、直前が属性の開始でないものだけを拾う。
    text = re.sub(
        r'(?<!href=")(?<!src=")(?<!>)(https?://[^\s<>"]+)',
        r'<a href="\1" class="loom-link-another">\1</a>',
        text,
    )

    # 斜体(3連クオート)を太字(2連クオート)より先に処理する
    text = re.sub(r"'''(.+?)'''", r"<i>\1</i>", text)
    text = re.sub(r"''(.+?)''", r"<b>\1</b>", text)

    # 打ち消し線 (ルール4)
    text = re.sub(r"%%(.+?)%%", r"<s>\1</s>", text)

    # 色 (ルール5)
    def _color(m):
        colors = [c.strip() for c in m.group(1).split(",")]
        content = m.group(2).strip()
        if len(colors) == 1:
            style = f"color: {_normalize_color(colors[0])};"
        else:
            style = (
                f"color: {_normalize_color(colors[0])}; "
                f"background-color: {_normalize_color(colors[1])};"
            )
        return f'<span style="{style}">{content}</span>'

    text = re.sub(r"&color\(([^)]+)\)\s*\{\s*(.*?)\s*\}", _color, text)

    # 改行 (ルール16)
    text = text.replace("&br;", "<br>")

    return text


def _normalize_color(c: str) -> str:
    if c.startswith("#") and len(c) in (4, 7):
        # #f00 のような3桁hexも rgb() へ展開する（見出しの整形後例に合わせる）
        hexdigits = c[1:]
        if len(hexdigits) == 3:
            r, g, b = (int(ch * 2, 16) for ch in hexdigits)
        else:
            r, g, b = (int(hexdigits[i : i + 2], 16) for i in (0, 2, 4))
        return f"rgb({r}, {g}, {b})"
    return c


def _extract_blocks(text, open_tag, close_tag):
    """{code}...{/code} や {quote}...{/quote} を抜き出し、プレースホルダに退避する。"""
    pattern = re.compile(re.escape(open_tag) + r"\n?(.*?)" + re.escape(close_tag), re.S)
    blocks = []

    def _store(m):
        blocks.append(m.group(1))
        return f"\x00BLOCK{len(blocks) - 1}\x00"

    text = pattern.sub(_store, text)
    return text, blocks


def convert(source: str) -> str:
    # ponytail: {code}ブロックはタグ挿入攻撃を避けるため個別に完全HTMLエスケープする。
    # それ以外の本文は &br;/&color()/[[a>b]] など自前記法が '&' '>' を使うため、
    # タグ注入対策として '<' だけをエスケープする（'&' '>' の全面エスケープはしない）。
    # 上限: 本文中の生の '>' や '&' はそのままHTMLへ流れるため、閉じタグ以外の
    # 意図的なHTML断片がユーザー入力に含まれると崩れうる。信頼できないHTMLを
    # そのまま公開表示する用途では html.escape を全面適用する版に強化すること。
    source, code_blocks = _extract_blocks(source, "{code}", "{/code}")
    code_blocks = [html.escape(c) for c in code_blocks]

    text = source.replace("<", "&lt;")
    text = _escape_literals(text)

    text, quote_blocks = _extract_blocks(text, "{quote}", "{/quote}")

    lines = text.split("\n")
    out = []
    heading_id = 0
    headings = []  # (level, text, id) 目次生成用
    list_stack = []  # [{"level": int, "tag": "ul"|"ol", "li_open": bool}]
    table_rows = []
    in_quote_run = False
    quote_lines = []

    def flush_table():
        nonlocal table_rows
        if table_rows:
            out.append("<table><tbody>")
            out.extend(table_rows)
            out.append("</tbody></table>")
            table_rows = []

    def flush_quote_run():
        nonlocal quote_lines, in_quote_run
        if quote_lines:
            out.append("<blockquote>" + "".join(f"<p>{_convert_inline(l)}</p>" for l in quote_lines) + "</blockquote>")
            quote_lines = []
        in_quote_run = False

    def close_list_stack():
        # 開いたままの<li>を閉じてから、そのレベルの<ul>/<ol>を閉じる。
        while list_stack:
            level_info = list_stack.pop()
            if level_info["li_open"]:
                out.append("</li>")
            out.append(f"</{level_info['tag']}>")

    i = 0
    while i < len(lines):
        raw = lines[i]

        m_block = re.match(r"^\x00BLOCK(\d+)\x00$", raw.strip())
        if m_block:
            close_list_stack()
            flush_table()
            flush_quote_run()
            idx = int(m_block.group(1))
            # code_blocks と quote_blocks はプレースホルダ生成順で混在しているため、
            # 抽出時に付けた通し番号を再利用し、まず code、次に quote の順で解決する。
            out.append(("__CODEBLOCK__", idx))
            i += 1
            continue

        m_head = re.match(r"^(\*{1,3})(.*)$", raw)
        m_bullet = re.match(r"^(-{1,3})(.*)$", raw)
        m_number = re.match(r"^\+(.*)$", raw)
        m_table = re.match(r"^\|(.*)\|(h)?$", raw)
        m_quote = re.match(r"^>\s?(.*)$", raw)

        if m_table:
            close_list_stack()
            flush_quote_run()
            is_header = bool(m_table.group(2))
            cells = m_table.group(1).split("|")
            row_html = ["<tr>"]
            for cell in cells:
                if cell.startswith("~"):
                    row_html.append(f"<th>{_convert_inline(cell[1:])}</th>")
                elif is_header:
                    row_html.append(f"<th>{_convert_inline(cell)}</th>")
                else:
                    row_html.append(f"<td>{_convert_inline(cell)}</td>")
            row_html.append("</tr>")
            table_rows.append("".join(row_html))
            i += 1
            continue
        else:
            flush_table()

        if m_quote:
            close_list_stack()
            in_quote_run = True
            quote_lines.append(m_quote.group(1))
            i += 1
            continue
        else:
            flush_quote_run()

        if m_head:
            close_list_stack()
            level = len(m_head.group(1))
            content = m_head.group(2)
            hid = f"loom-header-{heading_id}"
            headings.append((level, content.strip(), hid))
            heading_id += 1
            out.append(f'<h{level} id="{hid}">{_convert_inline(content)}</h{level}>')
            i += 1
            continue

        if m_bullet:
            level = len(m_bullet.group(1))
            content = m_bullet.group(2)
            # 現在より深いネストは、そのレベルの<li>と<ul>を閉じて抜ける。
            while list_stack and list_stack[-1]["level"] > level:
                level_info = list_stack.pop()
                if level_info["li_open"]:
                    out.append("</li>")
                out.append(f"</{level_info['tag']}>")
            if not list_stack or list_stack[-1]["level"] < level:
                # より深い階層へ入る: 親の<li>は閉じずに、その内側へ<ul>を入れ子にする。
                out.append("<ul>")
                list_stack.append({"level": level, "tag": "ul", "li_open": False})
            elif list_stack[-1]["li_open"]:
                # 同じ階層の次の項目: 直前の<li>を閉じてから新しい<li>を開く。
                out.append("</li>")
            out.append(f"<li>{_convert_inline(content)}")
            list_stack[-1]["li_open"] = True
            i += 1
            continue

        if m_number:
            content = m_number.group(1)
            if list_stack and len(list_stack) == 1 and list_stack[0]["tag"] == "ol":
                if list_stack[0]["li_open"]:
                    out.append("</li>")
            else:
                close_list_stack()
                out.append("<ol>")
                list_stack.append({"level": 1, "tag": "ol", "li_open": False})
            out.append(f"<li>{_convert_inline(content)}")
            list_stack[-1]["li_open"] = True
            i += 1
            continue

        close_list_stack()

        if raw.strip() == "#contents":
            out.append("\x00TOC\x00")
            i += 1
            continue

        if raw.strip() == "":
            out.append("<br>")
            i += 1
            continue

        out.append(_convert_inline(raw))
        i += 1

    close_list_stack()
    flush_table()
    flush_quote_run()

    # コード/引用ブロックは ("__CODEBLOCK__", idx) のタプルとして out に混在しているため、
    # 文字列化しつつプレースホルダを解決する。
    resolved = []
    for item in out:
        if isinstance(item, tuple) and item[0] == "__CODEBLOCK__":
            idx = item[1]
            if idx < len(code_blocks):
                resolved.append(f'<pre class="loom_code prettyprint">{code_blocks[idx]}</pre>')
            else:
                qidx = idx - len(code_blocks)
                lines_ = [l for l in quote_blocks[qidx].split("\n") if l.strip()]
                resolved.append("<blockquote>" + "".join(f"<p>{_convert_inline(l)}</p>" for l in lines_) + "</blockquote>")
        else:
            resolved.append(item)

    html_out = "".join(resolved)

    if "\x00TOC\x00" in html_out:
        html_out = html_out.replace("\x00TOC\x00", _build_toc(headings))

    html_out = _restore_literals(html_out)
    return html_out


def _build_toc(headings):
    # ルール15: h1〜h3(*/**/***)はフラットな<li>列として並べる。ルール表の
    # 「Header1/Header2/Header3」は実際にこのレベル差(1→2→3)でもネストしない
    # ことが示されているため、見出しレベルの差では入れ子にしない。
    # ("Header3-1"のような、より深いネストが生じる具体的な入力例は元のルール表に
    # 含まれておらず再現条件が不明なため、ここでは扱わない。)
    if not headings:
        return ""
    out = ['<ul class="loom-table-of-content">']
    for level, text, hid in headings:
        out.append(f'<li><a href="#{hid}"> {text}</a></li>')
    out.append("</ul>")
    return "".join(out)


def _run_self_tests() -> bool:
    cases = [
        ("''Bold''", "<b>Bold</b>"),
        ("'''Italic'''", "<i>Italic</i>"),
        ("%%Strike%%", "<s>Strike</s>"),
        ("aaa&br;bbb", "aaa<br>bbb"),
        ("BLG-95", '<button type="button" role="button" class="_trigger-text">BLG-95</button>'),
        ("[[WikiPageName]]", '<button type="button" role="button" class="_trigger-text">WikiPageName</button>'),
        ("[[Backlog>https://backlog.com/]]", '<a href="https://backlog.com/" class="loom-link-another">Backlog</a>'),
        ("#rev(11)", '<button type="button" role="button" class="_trigger-text">r11</button>'),
        (
            "#rev(app:abcdeabcde)",
            '<button type="button" role="button" class="_trigger-text">app:abcdeabcde</button>',
        ),
    ]
    ok = True
    for src, expected in cases:
        got = convert(src)
        if expected not in got:
            print(f"FAIL: convert({src!r}) -> {got!r}  (expected substring {expected!r})", file=sys.stderr)
            ok = False
    if ok:
        print("SUCCESS: all self-tests passed.", file=sys.stderr)
    return ok


def main():
    parser = argparse.ArgumentParser(description="Backlog記法をHTMLへ変換する")
    parser.add_argument("input", nargs="?", help="入力ファイル。'-' または省略時は標準入力。")
    parser.add_argument("--test", action="store_true", help="内部自己テストを実行する")
    args = parser.parse_args()

    if args.test:
        sys.exit(0 if _run_self_tests() else 1)

    if args.input and args.input != "-":
        with open(args.input, "r", encoding="utf-8") as f:
            source = f.read()
    else:
        source = sys.stdin.read()

    sys.stdout.write(convert(source))


if __name__ == "__main__":
    main()
