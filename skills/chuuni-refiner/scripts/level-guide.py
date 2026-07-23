#!/usr/bin/env python3
import argparse
import json
import sys

GUIDES = {
    "low": {
        "intensity": 1,
        "description": "自然な日本語を保った、控えめな劇的表現",
        "allowed": ["象徴語を1つ加える", "リズムを少し引き締める", "重い設定は加えない"],
        "avoid": ["封印された力", "終末規模の危機", "漢字複合語の多用"]
    },
    "medium": {
        "intensity": 2,
        "description": "実用性を保ちながら、厨二と明確に分かる表現",
        "allowed": ["影・運命・覚醒のモチーフ", "劇的な語句を1つ加える", "軽い特別な存在感"],
        "avoid": ["複数節にわたる設定の詰め込み", "読みにくい古風な文体"]
    },
    "high": {
        "intensity": 3,
        "description": "暗黒幻想的で大仰な、強い厨二表現",
        "allowed": ["封じられた力", "禁断の契約", "劇的な複合語", "芝居がかった文の区切り"],
        "avoid": ["事実の捏造", "元の意味の喪失"]
    },
    "max": {
        "intensity": 4,
        "description": "意図的に過剰な厨二表現",
        "allowed": ["終末規模の比喩", "名を与えた隠された力", "古代の誓約", "壮大な宣言"],
        "avoid": ["実在人物への嫌がらせ", "技術・事実の捏造", "元の意味からの完全な逸脱"]
    }
}

parser = argparse.ArgumentParser(description="厨二表現の強度ガイドをJSONで返す。")
parser.add_argument("--level", required=True, help="low、medium、high、max のいずれか")
args = parser.parse_args()
level = args.level.strip().lower()
if level not in GUIDES:
    print(f"エラー: 未対応のレベル '{args.level}'。low、medium、high、max のいずれかを指定してください。", file=sys.stderr)
    sys.exit(2)
print(json.dumps({"level": level, **GUIDES[level]}, ensure_ascii=False, indent=2))
