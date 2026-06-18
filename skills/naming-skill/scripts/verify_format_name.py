#!/usr/bin/env python3
"""Verify format_name.py against representative change-case spec examples."""
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).with_name("format_name.py")

CASES = [
    (["", "--style", "camelCase", "--max-words", "0"], ""),
    (["test", "--style", "camelCase", "--max-words", "0"], "test"),
    (["test", "--style", "PascalCase", "--max-words", "0"], "Test"),
    (["test string", "--style", "camelCase", "--max-words", "0"], "testString"),
    (["test string", "--style", "capitalCase", "--max-words", "0"], "Test String"),
    (["test string", "--style", "constantCase", "--max-words", "0"], "TEST_STRING"),
    (["test string", "--style", "dotCase", "--max-words", "0"], "test.string"),
    (["test string", "--style", "kebabCase", "--max-words", "0"], "test-string"),
    (["test string", "--style", "noCase", "--max-words", "0"], "test string"),
    (["test string", "--style", "pascalCase", "--max-words", "0"], "TestString"),
    (["test string", "--style", "pascalSnakeCase", "--max-words", "0"], "Test_String"),
    (["test string", "--style", "pathCase", "--max-words", "0"], "test/string"),
    (["test string", "--style", "sentenceCase", "--max-words", "0"], "Test string"),
    (["test string", "--style", "snakeCase", "--max-words", "0"], "test_string"),
    (["test string", "--style", "trainCase", "--max-words", "0"], "Test-String"),
    (["TestV2", "--style", "kebabCase", "--max-words", "0"], "test-v2"),
    (["TestV2", "--style", "kebabCase", "--separate-numbers", "--max-words", "0"], "test-v-2"),
    (["version 1.2.10", "--style", "camelCase", "--max-words", "0"], "version_1_2_10"),
    (["version 1.2.10", "--style", "pascalCase", "--max-words", "0"], "Version_1_2_10"),
    (["version 1.2.10", "--style", "camelCase", "--merge-ambiguous-characters", "--max-words", "0"], "version1210"),
    (["version 1.2.10", "--style", "pascalCase", "--merge-ambiguous-characters", "--max-words", "0"], "Version1210"),
    (["__typename", "--style", "camelCase", "--prefix-characters", "_", "--max-words", "0"], "__typename"),
    (["type__", "--style", "snakeCase", "--suffix-characters", "_", "--max-words", "0"], "type__"),
]


def run_case(args, expected):
    proc = subprocess.run([sys.executable, str(SCRIPT), *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    actual = proc.stdout.rstrip("\n")
    if proc.returncode != 0 or actual != expected:
        print("FAIL", file=sys.stderr)
        print(f"  args: {args}", file=sys.stderr)
        print(f"  returncode: {proc.returncode}", file=sys.stderr)
        print(f"  expected: {expected!r}", file=sys.stderr)
        print(f"  actual:   {actual!r}", file=sys.stderr)
        if proc.stderr:
            print(f"  stderr: {proc.stderr.strip()}", file=sys.stderr)
        return False
    return True


def main():
    failures = 0
    for args, expected in CASES:
        if not run_case(args, expected):
            failures += 1
    if failures:
        print(f"format_name verification failed: {failures}/{len(CASES)} cases", file=sys.stderr)
        return 1
    print(f"format_name verification passed: {len(CASES)} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
