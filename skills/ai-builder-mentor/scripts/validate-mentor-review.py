#!/usr/bin/env python3
"""Validate a completed AI builder mentor review."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_HEADINGS = [
    "Verdict",
    "Observations",
    "Mentor Diagnosis",
    "Three Hard Questions",
    "Smallest Experiment",
    "Distribution Loop",
    "Quality Bar",
    "Risks / Counterevidence",
    "Next Action",
    "Sources",
]

REQUIRED_TESTS = [
    "Contact with reality",
    "Small and sharp",
    "Behavior fit",
    "Workflow redesign",
    "Expertise and translation",
    "Distribution loop",
    "Human system",
]

REQUIRED_FIELDS = {
    "Smallest Experiment": [
        "Target user",
        "Single job",
        "Existing trigger",
        "Test action",
        "Behavior metric",
        "Success threshold",
        "Kill/change criterion",
        "Timebox",
    ],
    "Distribution Loop": [
        "Demonstration",
        "Teaching artifact",
        "Feedback source",
        "Planned refinement",
    ],
    "Quality Bar": [
        "Domain expert",
        "Good reference",
        "Bad reference",
        "Context passed to the agent",
        "Review and iteration method",
    ],
}

ALLOWED_STATUSES = {"Pass", "Needs work", "Unknown"}
VERDICT_PATTERN = re.compile(r"^(Conditional Go|Needs Work|Go|Stop)(?:\s|—|$)")


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)


def split_sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text, re.MULTILINE))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[match.group(1).strip()] = text[start:end].strip()
    return sections


def unresolved_placeholders(text: str) -> list[str]:
    """Reject all bracket tokens that are not Markdown links."""
    return re.findall(r"\[([^\]\n]+)\](?!\()", text)


def parse_diagnosis_rows(section: str) -> tuple[dict[str, list[str]], list[str]]:
    rows: dict[str, list[str]] = {}
    duplicates: list[str] = []
    for line in section.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        key = cells[0]
        if key not in REQUIRED_TESTS:
            continue
        if key in rows:
            duplicates.append(key)
        rows[key] = cells
    return rows, duplicates


def validate_named_fields(section_name: str, section: str) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_FIELDS[section_name]:
        match = re.search(
            rf"^[ \t]*-[ \t]*\*\*{re.escape(field)}:\*\*[ \t]*([^\n]*)$",
            section,
            re.MULTILINE,
        )
        if match is None:
            errors.append(f"Missing field in {section_name}: {field}")
        elif not match.group(1):
            errors.append(f"Empty field in {section_name}: {field}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate section content, diagnosis statuses, evidence labels, and sources."
    )
    parser.add_argument("review", help="Path to the completed Markdown mentor review")
    parser.add_argument(
        "--allow-empty-sources",
        action="store_true",
        help="Allow no URL only when Sources says 'No external sources used'.",
    )
    args = parser.parse_args()

    path = Path(args.review)
    if not path.is_file():
        fail(f"Review file does not exist: {path}")
        return 2

    text = path.read_text(encoding="utf-8")
    sections = split_sections(text)
    errors: list[str] = []

    for heading in REQUIRED_HEADINGS:
        if heading not in sections:
            errors.append(f"Missing required heading: ## {heading}")
        elif not sections[heading]:
            errors.append(f"Required section is empty: ## {heading}")

    placeholders = unresolved_placeholders(text)
    if placeholders:
        errors.append("Unresolved bracket placeholder(s): " + ", ".join(placeholders))

    verdict = sections.get("Verdict", "")
    first_verdict_line = next((line.strip() for line in verdict.splitlines() if line.strip()), "")
    if not VERDICT_PATTERN.match(first_verdict_line):
        errors.append(
            "The first substantive Verdict line must start with the exact token Go, Conditional Go, Needs Work, or Stop."
        )

    observations = sections.get("Observations", "")
    for label in ("Observation", "Inference", "Unknown"):
        if not re.search(rf"\*\*{label}:\*\*\s+\S", observations):
            errors.append(f"Observations must contain a non-empty **{label}:** item.")

    diagnosis = sections.get("Mentor Diagnosis", "")
    rows, duplicates = parse_diagnosis_rows(diagnosis)
    for duplicate in duplicates:
        errors.append(f"Duplicate diagnosis row: {duplicate}")
    for test in REQUIRED_TESTS:
        cells = rows.get(test)
        if cells is None:
            errors.append(f"Missing exact diagnosis row: {test}")
            continue
        if cells[1] not in ALLOWED_STATUSES:
            errors.append(f"Invalid status for {test}: {cells[1]!r}")
        if not cells[2] or not cells[3]:
            errors.append(f"Diagnosis row needs Evidence and Required change: {test}")

    questions = sections.get("Three Hard Questions", "")
    for number in (1, 2, 3):
        if not re.search(rf"^{number}\.\s+\S", questions, re.MULTILINE):
            errors.append(f"Missing non-empty hard question {number}.")

    for section_name in REQUIRED_FIELDS:
        errors.extend(validate_named_fields(section_name, sections.get(section_name, "")))

    sources = sections.get("Sources", "")
    urls = re.findall(r"https?://[^\s)]+", sources)
    if args.allow_empty_sources:
        if not urls and "No external sources used" not in sources:
            errors.append("Empty Sources requires the exact phrase: No external sources used")
    elif not urls:
        errors.append("Sources must contain at least one direct HTTP(S) URL.")
    if any("example.com" in url for url in urls):
        errors.append("Placeholder source URL detected: example.com")

    persona_patterns = [
        r"本人になりき",
        r"本人を演じ",
        r"本人の(?:声|口調|文体)で",
        r"特定人物として助言",
        r"speaking\s+as\s+the\s+person",
        r"imitat(?:e|ing)\s+the\s+person",
    ]
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in persona_patterns):
        errors.append("Persona imitation language detected; use a generalized mentor lens instead.")

    if errors:
        for error in errors:
            fail(error)
        print(f"FAILED: {len(errors)} validation error(s) in {path}", file=sys.stderr)
        return 1

    print(f"SUCCESS: Mentor review structure is valid: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
