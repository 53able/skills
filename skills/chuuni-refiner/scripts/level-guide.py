#!/usr/bin/env python3
import argparse
import json
import sys

GUIDES = {
    "low": {
        "intensity": 1,
        "description": "subtle drama; mostly natural Japanese",
        "allowed": ["one symbolic noun", "slight rhythm tightening", "no heavy lore"],
        "avoid": ["sealed powers", "apocalypse stakes", "too many kanji compounds"]
    },
    "medium": {
        "intensity": 2,
        "description": "recognizably chuuni but still usable",
        "allowed": ["shadow/fate/awakening motif", "one dramatic phrase", "light special-existence framing"],
        "avoid": ["multi-clause lore dumps", "unreadable archaic style"]
    },
    "high": {
        "intensity": 3,
        "description": "strong dark-fantasy grandiosity",
        "allowed": ["sealed force", "forbidden contract", "dramatic compounds", "theatrical sentence breaks"],
        "avoid": ["invented factual claims", "losing source meaning"]
    },
    "max": {
        "intensity": 4,
        "description": "deliberately excessive chuuni spectacle",
        "allowed": ["apocalypse-scale metaphor", "named hidden power", "ancient oath", "grand declaration"],
        "avoid": ["real-person harassment", "technical/factual fabrication", "complete semantic drift"]
    }
}

parser = argparse.ArgumentParser(description="Return a JSON intensity guide for chuuni refinement.")
parser.add_argument("--level", required=True, help="low, medium, high, or max")
args = parser.parse_args()
level = args.level.strip().lower()
if level not in GUIDES:
    print(f"ERROR: unsupported level '{args.level}'. Use low, medium, high, or max.", file=sys.stderr)
    sys.exit(2)
print(json.dumps({"level": level, **GUIDES[level]}, ensure_ascii=False, indent=2))
