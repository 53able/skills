#!/usr/bin/env python3
"""Emit the default publish workflow as Markdown (stdout). No arguments."""

WORKFLOW_MD = """## 既定フロー（要約）

1. **インプット** — 主題に関する材料を集める。量が足りないと質が出ない。
2. **誰に書くか** — 想定読者を一人に絞り、その人の疑問・状況をリサーチする。
3. **構成案** — 「誰に・何を伝えるか」「伝えたあとどうなってほしいか」だけを骨子にする。
4. **執筆と圧縮** — 下書き後、冗長さを削り読了負担を減らす。
5. **寝かせ** — 一晩置き、最初の読者として自分で通読してから公開する。
"""


def main() -> None:
    print(WORKFLOW_MD, end="")


if __name__ == "__main__":
    main()
