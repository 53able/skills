#!/usr/bin/env python3
"""Format a short English naming phrase using change-case-like rules.

The implementation mirrors the public change-case split/transform behavior used in
packages/change-case/src/index.spec.ts closely enough for naming work, while
keeping the local skill self-contained.
"""
import argparse
import sys
import unicodedata
from typing import Callable, List, Optional, Tuple

STYLE_ALIASES = {
    "kebab": "kebab", "kebab-case": "kebab", "kebabcase": "kebab", "param": "kebab", "param-case": "kebab",
    "snake": "snake", "snake_case": "snake", "snake-case": "snake", "snakecase": "snake",
    "camel": "camel", "camelcase": "camel", "camel-case": "camel",
    "pascal": "pascal", "pascalcase": "pascal", "pascal-case": "pascal",
    "constant": "constant", "constant_case": "constant", "constant-case": "constant", "constantcase": "constant", "upper-snake": "constant",
    "dot": "dot", "dot.case": "dot", "dot-case": "dot", "dotcase": "dot",
    "path": "path", "path/case": "path", "path-case": "path", "pathcase": "path",
    "train": "train", "train-case": "train", "traincase": "train",
    "capital": "capital", "capital-case": "capital", "capitalcase": "capital",
    "sentence": "sentence", "sentence-case": "sentence", "sentencecase": "sentence",
    "no": "no", "no-case": "no", "nocase": "no", "space": "no",
    "pascal-snake": "pascal_snake", "pascal_snake": "pascal_snake", "pascal-snake-case": "pascal_snake", "pascalsnakecase": "pascal_snake",
}


def is_letter(ch: str) -> bool:
    return bool(ch) and unicodedata.category(ch).startswith("L")


def is_lower(ch: str) -> bool:
    return is_letter(ch) and ch == ch.lower() and ch != ch.upper()


def is_upper(ch: str) -> bool:
    return is_letter(ch) and ch == ch.upper() and ch != ch.lower()


def is_digit(ch: str) -> bool:
    return ch.isdigit()


def is_word_char(ch: str) -> bool:
    return is_letter(ch) or is_digit(ch)


def split_chunk(chunk: str) -> List[str]:
    if not chunk:
        return []
    words: List[str] = []
    start = 0
    for i in range(1, len(chunk)):
        prev = chunk[i - 1]
        cur = chunk[i]
        nxt = chunk[i + 1] if i + 1 < len(chunk) else ""
        lower_upper = (is_lower(prev) or is_digit(prev)) and is_upper(cur)
        upper_upper = is_upper(prev) and is_upper(cur) and is_lower(nxt)
        if lower_upper or upper_upper:
            words.append(chunk[start:i])
            start = i
    words.append(chunk[start:])
    return words


def split_words(value: str) -> List[str]:
    chunks: List[str] = []
    cur: List[str] = []
    for ch in value.strip():
        if is_word_char(ch):
            cur.append(ch)
        elif cur:
            chunks.append("".join(cur))
            cur = []
    if cur:
        chunks.append("".join(cur))

    words: List[str] = []
    for chunk in chunks:
        words.extend(split_chunk(chunk))
    return words


def split_separate_numbers(value: str) -> List[str]:
    words = split_words(value)
    i = 0
    while i < len(words):
        word = words[i]
        split_at = None
        for j in range(len(word) - 1):
            ch, nxt = word[j], word[j + 1]
            # Mirrors change-case SPLIT_SEPARATE_NUMBER_RE: (digit before lowercase) or (letter before digit).
            if (is_digit(ch) and is_lower(nxt)) or (is_letter(ch) and is_digit(nxt)):
                split_at = j + 1
                break
        if split_at is not None:
            words[i:i + 1] = [word[:split_at], word[split_at:]]
        i += 1
    return words


def split_prefix_suffix(input_text: str, prefix_chars: str = "", suffix_chars: str = "", separate_numbers: bool = False) -> Tuple[str, List[str], str]:
    prefix_index = 0
    suffix_index = len(input_text)
    while prefix_index < len(input_text) and input_text[prefix_index] in prefix_chars:
        prefix_index += 1
    while suffix_index > prefix_index and input_text[suffix_index - 1] in suffix_chars:
        suffix_index -= 1
    core = input_text[prefix_index:suffix_index]
    split_fn: Callable[[str], List[str]] = split_separate_numbers if separate_numbers else split_words
    return input_text[:prefix_index], split_fn(core), input_text[suffix_index:]


def lower(word: str) -> str:
    return word.lower()


def upper(word: str) -> str:
    return word.upper()


def capital_transform(word: str) -> str:
    return upper(word[:1]) + lower(word[1:]) if word else word


def pascal_transform(word: str, index: int, merge_ambiguous: bool = False) -> str:
    if not word:
        return word
    if not merge_ambiguous and index > 0 and word[0].isdigit():
        return "_" + word[0] + lower(word[1:])
    return upper(word[0]) + lower(word[1:])


def apply_style(words: List[str], style: str, delimiter: Optional[str] = None, merge_ambiguous: bool = False) -> str:
    canonical = STYLE_ALIASES.get(style.strip().lower())
    if not canonical:
        raise ValueError(f"unsupported style: {style}")

    if canonical == "no":
        return (delimiter if delimiter is not None else " ").join(lower(w) for w in words)
    if canonical == "kebab":
        return (delimiter if delimiter is not None else "-").join(lower(w) for w in words)
    if canonical == "snake":
        return (delimiter if delimiter is not None else "_").join(lower(w) for w in words)
    if canonical == "dot":
        return (delimiter if delimiter is not None else ".").join(lower(w) for w in words)
    if canonical == "path":
        return (delimiter if delimiter is not None else "/").join(lower(w) for w in words)
    if canonical == "constant":
        return (delimiter if delimiter is not None else "_").join(upper(w) for w in words)
    if canonical == "capital":
        return (delimiter if delimiter is not None else " ").join(capital_transform(w) for w in words)
    if canonical == "train":
        return (delimiter if delimiter is not None else "-").join(capital_transform(w) for w in words)
    if canonical == "sentence":
        sep = delimiter if delimiter is not None else " "
        return sep.join(capital_transform(w) if i == 0 else lower(w) for i, w in enumerate(words))
    if canonical == "pascal_snake":
        return (delimiter if delimiter is not None else "_").join(capital_transform(w) for w in words)
    if canonical == "pascal":
        sep = delimiter if delimiter is not None else ""
        return sep.join(pascal_transform(w, i, merge_ambiguous) for i, w in enumerate(words))
    if canonical == "camel":
        sep = delimiter if delimiter is not None else ""
        return sep.join(lower(w) if i == 0 else pascal_transform(w, i, merge_ambiguous) for i, w in enumerate(words))
    raise AssertionError(canonical)


def format_name(input_text: str, style: str, delimiter: Optional[str] = None, prefix_chars: str = "", suffix_chars: str = "", separate_numbers: bool = False, merge_ambiguous: bool = False) -> str:
    prefix, words, suffix = split_prefix_suffix(input_text, prefix_chars, suffix_chars, separate_numbers)
    return prefix + apply_style(words, style, delimiter, merge_ambiguous) + suffix


def main() -> int:
    parser = argparse.ArgumentParser(description="Format a short English naming phrase using change-case-like rules.")
    parser.add_argument("phrase", help="English words to format")
    parser.add_argument("--style", required=True, help="case style, e.g. kebab-case or snake_case")
    parser.add_argument("--max-words", type=int, default=4, help="maximum words allowed; use 0 to disable")
    parser.add_argument("--extension", default="", help="optional extension without or with leading dot")
    parser.add_argument("--delimiter", default=None, help="override delimiter, matching change-case options.delimiter")
    parser.add_argument("--separate-numbers", action="store_true", help="split letters and numbers more aggressively")
    parser.add_argument("--merge-ambiguous-characters", action="store_true", help="merge number words in camel/pascal case")
    parser.add_argument("--prefix-characters", default="", help="characters to preserve at the start")
    parser.add_argument("--suffix-characters", default="", help="characters to preserve at the end")
    args = parser.parse_args()

    prefix, words, suffix = split_prefix_suffix(args.phrase, args.prefix_characters, args.suffix_characters, args.separate_numbers)
    if args.max_words and len(words) > args.max_words:
        print(f"Too many words: {len(words)} > {args.max_words}. Revise the phrase before formatting.", file=sys.stderr)
        return 3
    try:
        name = prefix + apply_style(words, args.style, args.delimiter, args.merge_ambiguous_characters) + suffix
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        print("Read references/change-case-formats.md for supported styles.", file=sys.stderr)
        return 4

    ext = args.extension.strip()
    if ext:
        ext = ext if ext.startswith(".") else "." + ext
    print(name + ext)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
