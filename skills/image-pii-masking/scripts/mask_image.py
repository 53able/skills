#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10,<3.13"
# dependencies = [
#   "presidio-image-redactor==0.0.60",
#   "presidio-analyzer==2.2.364",
#   "pillow>=10.0,<14",
#   "spacy>=3.8,<3.9",
#   "ja_core_news_sm @ https://github.com/explosion/spacy-models/releases/download/ja_core_news_sm-3.8.0/ja_core_news_sm-3.8.0-py3-none-any.whl",
# ]
# ///
"""Detect and mask sensitive text regions in an image (local, offline).

Run with `uv run scripts/mask_image.py ...` so dependencies resolve into an
isolated ephemeral environment. The Tesseract binary is a system dependency and
is NOT isolated by uv; see SKILL.md.

Pipeline: OCR (Tesseract) -> PII detection (Presidio + JP pattern recognizers)
-> opaque fill of matching pixel regions -> re-OCR verification.

Outputs a masked image, a JSON detection report, and a non-zero exit code when
verification fails, so callers can gate publication on the check.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

from PIL import Image, ImageDraw

# --- Japanese-oriented pattern recognizers -----------------------------------
# Deliberately conservative regexes. Recall over precision is the intent:
# false positives are cheap (review step), misses are not.
JP_PATTERNS: dict[str, list[tuple[str, str, float]]] = {
    # OCR inserts word separators and misreads characters, so patterns stay
    # tolerant of stray spaces rather than assuming clean text.
    "JP_PHONE": [
        ("jp-phone-hyphen", r"\b0\d{1,4}\s?-\s?\d{1,4}\s?-\s?\d{3,4}\b", 0.6),
        ("jp-mobile-plain", r"\b0[789]0\d{8}\b", 0.5),
        ("jp-phone-intl", r"\+\s?81[-\s]?\d{1,4}[-\s]?\d{1,4}[-\s]?\d{3,4}", 0.6),
    ],
    "JP_POSTAL_CODE": [
        ("jp-postal", r"(?:〒\s?)?\b\d{3}\s?-\s?\d{4}\b", 0.4),
    ],
    "JP_MYNUMBER": [
        ("jp-mynumber", r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", 0.35),
    ],
    "JP_ADDRESS": [
        (
            "jp-address",
            r"[^\s、。:：]{1,10}\s?(?:都|道|府|県)\s?[^、。:：]{0,14}?\s?(?:市|区|町|村)\s?[^、。:：]{0,20}",
            0.5,
        ),
        ("jp-banchi", r"\d{1,4}\s?[-−]\s?\d{1,4}\s?[-−]\s?\d{1,4}\s?(?:番地|号)?", 0.35),
    ],
    # Deliberately looser than the strict RFC-ish email recognizer: OCR damages
    # TLDs ("example.co.jp" -> "example.coJjp") and strict patterns then miss.
    "EMAIL_LOOSE": [
        ("email-loose", r"[A-Za-z0-9._%+\-]{2,}\s?@\s?[A-Za-z0-9.\-]{2,}", 0.6),
    ],
    "SECRET_TOKEN": [
        ("aws-access-key", r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b", 0.9),
        ("gh-token", r"\bgh[pousr]_[A-Za-z0-9]{20,}\b", 0.9),
        ("openai-key", r"\bsk-[A-Za-z0-9_-]{20,}\b", 0.9),
        ("slack-token", r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b", 0.9),
        ("bearer", r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}", 0.8),
        ("jwt", r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b", 0.9),
        ("pem-header", r"-{3,}\s?BEGIN [A-Z ]*PRIVATE KEY\s?-{3,}", 0.95),
    ],
}

DEFAULT_PROTECTED_LABELS = [
    # Common Japanese field labels. These are protected from entity boxes;
    # values can still be masked by the adjacent value box or a pattern.
    "氏名", "フリガナ", "生年月日", "郵便番号", "住所", "所在地",
    "電話", "電話番号", "携帯", "メール", "起票者", "会社",
    "件名", "契約ID", "契約状態", "開始日", "月額", "累計売上",
    "更新区分", "プラン", "請求先", "振込先", "合計", "金額",
    "問い合わせ本文", "添付", "エラーログ抜粋",
]


DEFAULT_ENTITIES = [
    "PERSON",
    "LOCATION",
    "EMAIL_ADDRESS",
    "EMAIL_LOOSE",
    "CREDIT_CARD",
    "IBAN_CODE",
    "IP_ADDRESS",
    "CRYPTO",
    # DATE_TIME is intentionally excluded: it matches literal field labels
    # ("生年月日" -> "年 月 日") and unrelated business dates. Use
    # --mask-right-of 生年月日 to mask a birth date value precisely.
    "JP_PHONE",
    "JP_POSTAL_CODE",
    "JP_MYNUMBER",
    "JP_ADDRESS",
    "SECRET_TOKEN",
]


@dataclass
class Detection:
    entity_type: str
    text: str
    score: float
    left: int
    top: int
    width: int
    height: int


def build_analyzer(language: str, deny_list: list[str], extra_patterns: dict[str, str]):
    from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
    from presidio_analyzer.nlp_engine import NlpEngineProvider
    from presidio_analyzer.predefined_recognizers import (
        EmailRecognizer,
        CreditCardRecognizer,
        IpRecognizer,
        IbanRecognizer,
        CryptoRecognizer,
        SpacyRecognizer,
    )
    from presidio_analyzer import RecognizerRegistry

    spacy_model = "ja_core_news_sm" if language == "ja" else "en_core_web_sm"
    nlp_conf = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": language, "model_name": spacy_model}],
        "ner_model_configuration": {
            "model_to_presidio_entity_mapping": {
                "PERSON": "PERSON",
                "PSN": "PERSON",
                "GPE": "LOCATION",
                "LOC": "LOCATION",
                "FAC": "LOCATION",
                "ORG": "ORGANIZATION",
                "DATE": "DATE_TIME",
                "TIME": "DATE_TIME",
                "MONEY": "MONEY",
            },
            "low_score_entity_names": [],
            "labels_to_ignore": ["CARDINAL", "ORDINAL", "QUANTITY", "PERCENT"],
        },
    }
    nlp_engine = NlpEngineProvider(nlp_configuration=nlp_conf).create_engine()

    registry = RecognizerRegistry(supported_languages=[language])
    for cls in (
        EmailRecognizer,
        CreditCardRecognizer,
        IpRecognizer,
        IbanRecognizer,
        CryptoRecognizer,
    ):
        registry.add_recognizer(cls(supported_language=language))
    registry.add_recognizer(SpacyRecognizer(supported_language=language))

    for entity, specs in JP_PATTERNS.items():
        patterns = [Pattern(name=n, regex=r, score=s) for n, r, s in specs]
        registry.add_recognizer(
            PatternRecognizer(
                supported_entity=entity,
                patterns=patterns,
                supported_language=language,
            )
        )
    for entity, regex in extra_patterns.items():
        registry.add_recognizer(
            PatternRecognizer(
                supported_entity=entity,
                patterns=[Pattern(name=f"custom-{entity}", regex=regex, score=0.9)],
                supported_language=language,
            )
        )
    if deny_list:
        registry.add_recognizer(
            PatternRecognizer(
                supported_entity="DENY_LIST",
                deny_list=deny_list,
                supported_language=language,
            )
        )

    return AnalyzerEngine(
        nlp_engine=nlp_engine,
        registry=registry,
        supported_languages=[language],
    )


def run_ocr(image: Image.Image, args, psm: str, upscale: float):
    """Return (ocr, ocr_result_dict, reconstructed_text) for one OCR pass.

    Upscaling before OCR measurably improves recall on dense full-page
    screenshots, so bounding boxes are scaled back to original coordinates.
    """
    from presidio_image_redactor import ImageAnalyzerEngine, TesseractOCR

    ocr = TesseractOCR()
    target = image
    if upscale != 1.0:
        target = image.resize(
            (int(image.width * upscale), int(image.height * upscale)),
            Image.LANCZOS,
        )
    result = ocr.perform_ocr(target, lang=args.lang, config=f"--oem 1 --psm {psm}")
    if upscale != 1.0:
        inv = 1.0 / upscale
        for key in ("left", "top", "width", "height"):
            result[key] = [int(round(v * inv)) for v in result[key]]
    result = ImageAnalyzerEngine.remove_space_boxes(result)
    if args.ocr_threshold > 0:
        result = ImageAnalyzerEngine.threshold_ocr_result(result, args.ocr_threshold)
    return ocr, result, ocr.get_text_from_ocr_dict(result)


def normalize_label(text: str) -> str:
    import re
    return re.sub(r"\s+", "", str(text)).strip(" :：")


def protected_label_boxes(ocr_result: dict, labels: list[str]) -> list[tuple[int, int, int, int]]:
    """Find OCR boxes belonging to known labels, preserving them during masking."""
    words = [
        {
            "text": normalize_label(t),
            "left": int(l), "top": int(tp), "width": int(w), "height": int(h),
        }
        for t, l, tp, w, h in zip(
            ocr_result["text"], ocr_result["left"], ocr_result["top"],
            ocr_result["width"], ocr_result["height"],
        )
        if normalize_label(t)
    ]
    lines: list[list[dict]] = []
    for word in sorted(words, key=lambda d: (d["top"], d["left"])):
        center = word["top"] + word["height"] / 2
        for line in lines:
            ref = line[0]
            if ref["top"] - 6 <= center <= ref["top"] + ref["height"] + 6:
                line.append(word)
                break
        else:
            lines.append([word])

    targets = [normalize_label(label) for label in labels if normalize_label(label)]
    boxes: list[tuple[int, int, int, int]] = []
    for line in lines:
        line.sort(key=lambda d: d["left"])
        joined = ""
        spans = []
        for word in line:
            start = len(joined)
            joined += word["text"]
            spans.append((start, len(joined), word))
        for label in targets:
            start = 0
            while True:
                idx = joined.find(label, start)
                if idx < 0:
                    break
                end = idx + len(label)
                covering = [w for s, e, w in spans if s < end and e > idx]
                if covering:
                    x0 = min(w["left"] for w in covering)
                    y0 = min(w["top"] for w in covering)
                    x1 = max(w["left"] + w["width"] for w in covering)
                    y1 = max(w["top"] + w["height"] for w in covering)
                    boxes.append((x0, y0, x1, y1))
                start = max(end, idx + 1)
    return boxes


def overlaps_protected_label(result, protected: list[tuple[int, int, int, int]]) -> bool:
    """Reject a detection box when it substantially overlaps a protected label."""
    rx0, ry0 = int(result.left), int(result.top)
    rx1, ry1 = rx0 + int(result.width), ry0 + int(result.height)
    area = max(1, (rx1 - rx0) * (ry1 - ry0))
    for lx0, ly0, lx1, ly1 in protected:
        ix = max(0, min(rx1, lx1) - max(rx0, lx0))
        iy = max(0, min(ry1, ly1) - max(ry0, ly0))
        if ix * iy / area >= 0.20:
            return True
    return False


def label_anchored_boxes(image: Image.Image, args) -> list[Detection]:
    """Mask the value to the right of a given field label.

    Entity-based detection is blunt for label/value layouts: DATE_TIME masks the
    literal label characters and unrelated dates elsewhere on the page. Anchoring
    on the label instead masks only the value cell and leaves the label readable.

    Spec format: LABEL[:WIDTH]  (WIDTH defaults to 320px)
    """
    if not args.mask_right_of:
        return []

    _, ocr_result, _ = run_ocr(image, args, args.psm, args.anchor_upscale)
    words = [
        {
            "text": str(t).strip(),
            "left": int(l),
            "top": int(tp),
            "width": int(w),
            "height": int(h),
        }
        for t, l, tp, w, h in zip(
            ocr_result["text"],
            ocr_result["left"],
            ocr_result["top"],
            ocr_result["width"],
            ocr_result["height"],
        )
        if str(t).strip()
    ]

    # Group into visual lines by vertical overlap of the word center.
    lines: list[list[dict]] = []
    for w in sorted(words, key=lambda d: (d["top"], d["left"])):
        center = w["top"] + w["height"] / 2
        for line in lines:
            ref = line[0]
            if ref["top"] - 6 <= center <= ref["top"] + ref["height"] + 6:
                line.append(w)
                break
        else:
            lines.append([w])

    out: list[Detection] = []
    for spec in args.mask_right_of:
        label, _, width_s = spec.rpartition(":")
        if not label:  # no colon given
            label, width = spec, 320
        else:
            width = int(width_s)
        for line in lines:
            line.sort(key=lambda d: d["left"])
            joined = ""
            spans: list[tuple[int, int, dict]] = []
            for w in line:
                spans.append((len(joined), len(joined) + len(w["text"]), w))
                joined += w["text"]
            idx = joined.find(label)
            if idx < 0:
                continue
            end = idx + len(label)
            covering = [w for s, e, w in spans if s < end and e > idx]
            if not covering:
                continue
            anchor = max(covering, key=lambda w: w["left"] + w["width"])
            tops = [w["top"] for w in line]
            bottoms = [w["top"] + w["height"] for w in line]
            out.append(
                Detection(
                    entity_type="LABEL_VALUE",
                    text=f"right-of:{label}",
                    score=1.0,
                    left=anchor["left"] + anchor["width"] + 4,
                    top=min(tops) - 2,
                    width=width,
                    height=max(bottoms) - min(tops) + 4,
                )
            )
    return out


def analyze(image: Image.Image, analyzer, args) -> tuple[list[Detection], list[dict]]:
    """Union detections across OCR passes.

    A single Tesseract configuration silently drops regions: page-segmentation
    mode changes reading order, which breaks some patterns while fixing others.
    Boxes only ever add masking, so the union is the safe combination.
    """
    from presidio_image_redactor import ImageAnalyzerEngine

    entities = list(args.entities) if args.entities else list(DEFAULT_ENTITIES)
    if args.deny_list_file:
        entities.append("DENY_LIST")
    entities.extend(kv.split("=", 1)[0] for kv in args.extra_pattern)

    dets: list[Detection] = []
    seen: set[tuple] = set()
    pass_info: list[dict] = []
    for spec in args.ocr_pass:
        psm, _, up = spec.partition(":")
        upscale = float(up) if up else 1.0
        ocr, ocr_result, text = run_ocr(image, args, psm.strip(), upscale)
        engine = ImageAnalyzerEngine(analyzer_engine=analyzer, ocr=ocr)
        results = analyzer.analyze(
            text=text,
            language=args.language,
            entities=entities,
            score_threshold=args.threshold,
            allow_list=args.allow_list,
        )
        bboxes = engine.map_analyzer_results_to_bounding_boxes(
            results, ocr_result, text, args.allow_list
        )
        protected = protected_label_boxes(
            ocr_result,
            DEFAULT_PROTECTED_LABELS + (args.protected_labels or []),
        )
        filtered = [r for r in bboxes if not overlaps_protected_label(r, protected)]
        added = 0
        for r in filtered:
            key = (r.entity_type, int(r.left), int(r.top), int(r.width), int(r.height))
            if key in seen:
                continue
            seen.add(key)
            added += 1
            dets.append(
                Detection(
                    entity_type=r.entity_type,
                    text=text[r.start : r.end].strip(),
                    score=round(float(r.score), 3),
                    left=int(r.left),
                    top=int(r.top),
                    width=int(r.width),
                    height=int(r.height),
                )
            )
        pass_info.append(
            {
                "psm": psm.strip(),
                "upscale": upscale,
                "ocr_text_length": len(text),
                "boxes": len(bboxes),
                "protected_label_boxes": len(protected),
                "filtered_label_boxes": len(bboxes) - len(filtered),
                "new_boxes": added,
            }
        )
    return dets, pass_info


def render(image: Image.Image, dets: list[Detection], args) -> Image.Image:
    out = image.convert("RGB").copy()
    draw = ImageDraw.Draw(out)
    fill = tuple(int(v) for v in args.fill.split(","))
    for d in dets:
        # Explicit regions (--mask-box, --mask-right-of) are honored exactly.
        # Padding them would eat into the neighbouring label the caller asked
        # to keep readable.
        pad = 0 if d.entity_type in ("MANUAL", "LABEL_VALUE") else args.pad
        x0 = max(0, d.left - pad)
        y0 = max(0, d.top - pad)
        # A negative --pad shrinks boxes and can invert them; clamp to a valid
        # rectangle so rendering never raises and the report is always written.
        x1 = max(x0 + 1, min(out.width, d.left + d.width + pad))
        y1 = max(y0 + 1, min(out.height, d.top + d.height + pad))
        box = (x0, y0, x1, y1)
        if args.dry_run:
            draw.rectangle(box, outline=(255, 0, 0), width=2)
        else:
            draw.rectangle(box, fill=fill)
    return out


def verify(masked: Image.Image, dets: list[Detection], args) -> list[dict]:
    """Re-OCR the masked image and report any detected string that survived."""
    from presidio_image_redactor import TesseractOCR

    ocr = TesseractOCR()
    data = ocr.perform_ocr(
        masked, lang=args.lang, config=f"--oem 1 --psm {args.psm}"
    )
    text = "".join(str(t) for t in data.get("text", []) if str(t).strip())
    text = "".join(text.split())
    leaks = []
    for d in dets:
        needle = "".join(d.text.split())
        if len(needle) >= 4 and needle in text:
            leaks.append({"entity_type": d.entity_type, "text": d.text})
    return leaks


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path)
    p.add_argument("-o", "--output", type=Path, required=True)
    p.add_argument(
        "--profile",
        choices=["standard", "financial"],
        default="standard",
        help="Masking profile; financial adds invoice amounts and payment fields",
    )
    p.add_argument("--report", type=Path, help="JSON detection report path")
    p.add_argument("--lang", default="jpn+eng", help="Tesseract OCR languages")
    p.add_argument("--language", default="ja", help="Presidio analyzer language")
    p.add_argument(
        "--ocr-pass",
        action="append",
        default=None,
        metavar="PSM[:UPSCALE]",
        help="OCR pass config, repeatable. Default: 3:2 and 6:1",
    )
    p.add_argument(
        "--psm",
        default="6",
        help="PSM used by the verification re-OCR pass",
    )
    p.add_argument(
        "--mask-box",
        action="append",
        default=[],
        metavar="X,Y,W,H",
        help="Always mask this region regardless of detection, repeatable",
    )
    p.add_argument(
        "--mask-right-of",
        action="append",
        default=[],
        metavar="LABEL[:WIDTH]",
        help="Mask the value cell right of a field label, keeping the label readable",
    )
    p.add_argument(
        "--anchor-upscale",
        type=float,
        default=2.0,
        help="Upscale used by the --mask-right-of anchor OCR pass",
    )
    p.add_argument("--entities", nargs="*", help="Override entity list")
    p.add_argument("--threshold", type=float, default=0.35)
    p.add_argument(
        "--ocr-threshold",
        type=float,
        default=0,
        help="Drop OCR words below this confidence (0 disables)",
    )
    p.add_argument("--pad", type=int, default=3, help="Extra pixels around each box")
    p.add_argument("--fill", default="0,0,0", help="Opaque fill color R,G,B")
    p.add_argument("--allow-list", nargs="*", default=[], help="Strings never masked")
    p.add_argument(
        "--protected-label",
        dest="protected_labels",
        action="append",
        default=None,
        help="Additional label text to protect; repeatable (added to defaults)",
    )
    p.add_argument("--deny-list-file", type=Path, help="One literal string per line")
    p.add_argument(
        "--extra-pattern",
        action="append",
        default=[],
        metavar="ENTITY=REGEX",
        help="Additional regex recognizer, repeatable",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Outline candidates instead of filling them (for human review)",
    )
    p.add_argument("--no-verify", action="store_true")
    args = p.parse_args()

    if args.profile == "financial":
        # Financial data is not universally PII, so keep it opt-in. Use
        # label-anchored boxes for invoice party/payment fields and tolerant
        # patterns for OCR variants of currency and account numbers.
        args.extra_pattern.extend([
            r"JP_MONEY=[0-9][0-9,\. ]{2,}\s?円",
            r"BANK_ACCOUNT=\b\d{7,8}\b",
        ])
        args.mask_right_of.extend([
            "請求先:400",
            "振込先:400",
        ])

    deny_list: list[str] = []
    if args.deny_list_file:
        deny_list = [
            ln.strip()
            for ln in args.deny_list_file.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
    extra = dict(kv.split("=", 1) for kv in args.extra_pattern)
    if not args.ocr_pass:
        args.ocr_pass = ["3:2", "6:1"]

    image = Image.open(args.input)
    analyzer = build_analyzer(args.language, deny_list, extra)
    dets, pass_info = analyze(image, analyzer, args)
    manual = []
    for spec in args.mask_box:
        x, y, w, h = (int(v) for v in spec.split(","))
        manual.append(Detection("MANUAL", "", 1.0, x, y, w, h))
    manual.extend(label_anchored_boxes(image, args))
    out = render(image, dets + manual, args)

    # PNG output drops EXIF/GPS metadata that PII masking must not preserve.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.save(args.output, format="PNG")

    leaks: list[dict] = []
    if not args.dry_run and not args.no_verify:
        leaks = verify(out, dets, args)

    report = {
        "input": str(args.input),
        "output": str(args.output),
        "mode": "dry-run" if args.dry_run else "masked",
        "ocr_lang": args.lang,
        "analyzer_language": args.language,
        "profile": args.profile,
        "threshold": args.threshold,
        "ocr_passes": pass_info,
        "detection_count": len(dets),
        "manual_box_count": len(manual),
        "detections": [asdict(d) for d in dets + manual],
        "verification": {
            "ran": bool(leaks) or (not args.dry_run and not args.no_verify),
            "leaks": leaks,
        },
    }
    if args.report:
        args.report.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    json.dump(
        {k: report[k] for k in ("mode", "detection_count", "output", "verification")},
        sys.stdout,
        ensure_ascii=False,
    )
    print()

    if leaks:
        print(f"VERIFY FAILED: {len(leaks)} detected string(s) still readable", file=sys.stderr)
        return 2
    if not dets and not manual:
        print("NO DETECTIONS: treat as unverified, review manually", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
