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
"""Self-test for mask_image.py.

Generates a synthetic Japanese CRM screenshot with known PII positions, runs the
documented workflow, and asserts pixel-level outcomes plus exit-code contracts.

Run after changing mask_image.py, upgrading Tesseract/Presidio/spaCy, or before
trusting the tool on real data:

    uv run scripts/selftest.py [--workdir DIR] [--keep]

Exit code 0 means every check passed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
MASK = HERE / "mask_image.py"

FONT_GO = "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc"
FONT_GB = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
FONT_MONO = "/System/Library/Fonts/Menlo.ttc"
FONT_ASCII = "/System/Library/Fonts/Supplemental/Arial.ttf"

# Regions must be masked: every original ink pixel has to change.
MUST_MASK = [
    ("氏名の値", (178, 138, 272, 166)),
    ("フリガナの値", (178, 170, 410, 198)),
    ("生年月日の値", (182, 204, 332, 226)),
    ("郵便番号の値", (178, 234, 300, 260)),
    ("住所の値", (178, 266, 542, 294)),
    ("電話番号の値", (178, 298, 338, 324)),
    ("メールの値", (178, 330, 452, 356)),
    ("担当営業の値", (178, 362, 270, 388)),
    ("CRM_API_KEY行", (44, 464, 516, 490)),
    ("AWSキー行", (44, 494, 428, 520)),
    ("DB_HOST/DB_USER行", (44, 524, 448, 550)),
    ("WEBHOOK行のトークン部", (348, 554, 736, 580)),
]

# Regions must stay readable: no original ink pixel may be altered.
MUST_KEEP = [
    ("ラベル『氏名』", (44, 138, 92, 166)),
    ("ラベル『生年月日』", (44, 204, 118, 228)),
    ("ラベル『住所』", (44, 266, 92, 294)),
    ("ラベル『メール』", (44, 330, 116, 356)),
    ("開始日の値(非PII)", (738, 204, 892, 226)),
    ("累計売上の値(非PII)", (738, 266, 872, 292)),
    ("契約IDの値(非PII)", (738, 330, 912, 356)),
    ("契約状態の値(非PII)", (738, 170, 790, 196)),
    ("プランの値(非PII)", (738, 138, 902, 164)),
    ("ヘッダタイトル", (24, 16, 400, 46)),
    ("WEBHOOK=前半", (44, 554, 344, 580)),
]

LEFT_ROWS = [
    ("氏名", "田中 太郎"),
    ("フリガナ", "タナカ タロウ"),
    ("生年月日", "1985年4月12日"),
    ("郵便番号", "〒150-0041"),
    ("住所", "東京都渋谷区神南1-2-3 ハイツ渋谷402"),
    ("電話番号", "090-1234-5678"),
    ("メール", "taro.tanaka@example.co.jp"),
    ("担当営業", "鈴木 花子"),
]
RIGHT_ROWS = [
    ("プラン", "エンタープライズ"),
    ("契約状態", "有効"),
    ("開始日", "2024年10月1日"),
    ("月額", "480,000 円"),
    ("累計売上", "5,760,000 円"),
    ("更新区分", "自動更新"),
    ("契約ID", "CT-2024-000871"),
    ("口座番号", "1234567"),
]
SECRET_ROWS = [
    "CRM_API_KEY=sk-abcdefghijklmnopqrstuvwxyz012345",
    "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE",
    "DB_HOST=10.0.14.203    DB_USER=crm_admin",
    "WEBHOOK=https://hooks.example.com/T0A1B2C3/xoxb-9876543210-abcdefghij",
]


def build_fixture(path: Path) -> None:
    f_h1 = ImageFont.truetype(FONT_GB, 26)
    f_card = ImageFont.truetype(FONT_GB, 20)
    f_lbl = ImageFont.truetype(FONT_GO, 18)
    f_txt = ImageFont.truetype(FONT_GO, 20)
    f_mono = ImageFont.truetype(FONT_MONO, 16)
    f_small = ImageFont.truetype(FONT_GO, 15)

    img = Image.new("RGB", (1000, 620), "#f5f6f8")
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 1000, 58), fill="#243447")
    d.text((24, 16), "顧客管理システム  /  契約詳細", fill="white", font=f_h1)
    d.text((790, 22), "ログイン: 管理者", fill="#c8d2dd", font=f_small)

    for x0, x1, title, rows, lx, vx in (
        (24, 560, "契約者情報", LEFT_ROWS, 44, 178),
        (584, 976, "契約サマリ", RIGHT_ROWS, 604, 738),
    ):
        d.rectangle((x0, 82, x1, 400), fill="white", outline="#dfe3e8")
        d.text((lx, 100), title, fill="#243447", font=f_card)
        y = 140
        for label, value in rows:
            d.text((lx, y), label, fill="#7b8794", font=f_lbl)
            d.text((vx, y - 2), value, fill="#1f2933", font=f_txt)
            y += 32

    d.rectangle((24, 420, 976, 596), fill="#1f2933")
    d.text((44, 436), "連携設定（環境変数）", fill="#9aa5b1", font=f_small)
    y = 464
    for line in SECRET_ROWS:
        d.text((44, y), line, fill="#7ee2b8", font=f_mono)
        y += 30
    img.save(path)


def build_clean(path: Path) -> None:
    img = Image.new("RGB", (520, 120), "white")
    ImageDraw.Draw(img).text(
        (20, 44), "Build succeeded in 12s", fill="black",
        font=ImageFont.truetype(FONT_ASCII, 24),
    )
    img.save(path)


def run(args: list[str]) -> tuple[int, str]:
    p = subprocess.run(
        [sys.executable, str(MASK), *args], capture_output=True, text=True
    )
    return p.returncode, p.stdout + p.stderr


def pixels(img: Image.Image) -> list:
    """Pillow 12 renamed getdata(); support both without deprecation noise."""
    getter = getattr(img, "get_flattened_data", None) or img.getdata
    return list(getter())


def ink_stats(before: Image.Image, after: Image.Image, box) -> tuple[int, int, int]:
    """Return (ink_pixels, ink_unchanged, ink_altered) inside box."""
    b = before.crop(box)
    a = after.crop(box)
    bg = Counter(pixels(b)).most_common(1)[0][0]
    ink = unchanged = altered = 0
    for pb, pa in zip(pixels(b), pixels(a)):
        if sum(abs(x - y) for x, y in zip(pb, bg)) > 90:
            ink += 1
            if pb == pa:
                unchanged += 1
            else:
                altered += 1
    return ink, unchanged, altered


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", type=Path)
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()

    tmp = a.workdir or Path(tempfile.mkdtemp(prefix="mask-selftest-"))
    tmp.mkdir(parents=True, exist_ok=True)
    before_p, clean_p = tmp / "before.png", tmp / "clean.png"
    build_fixture(before_p)
    build_clean(clean_p)
    (tmp / "deny.txt").write_text("タナカ\nタロウ\ncrm_admin\n", encoding="utf-8")

    sys.path.insert(0, str(HERE))
    import mask_image as m  # noqa: E402

    checks: list[tuple[bool, str]] = []

    def check(ok: bool, label: str, detail: str = "") -> None:
        checks.append((ok, f"{label}{(' — ' + detail) if detail else ''}"))

    # 1. Defaults must not request DATE_TIME (it masks field labels).
    check(
        "DATE_TIME" not in m.DEFAULT_ENTITIES,
        "既定エンティティに DATE_TIME を含まない",
        f"既定={len(m.DEFAULT_ENTITIES)}件",
    )

    # 2. Full documented workflow.
    out_p, rep_p = tmp / "out.png", tmp / "out.json"
    code, log = run([
        str(before_p), "-o", str(out_p), "--report", str(rep_p), "--pad", "4",
        "--deny-list-file", str(tmp / "deny.txt"),
        "--extra-pattern", r"DB_CRED=DB_USER=\S+",
        "--mask-box", "176,166,230,30",
        "--mask-right-of", "生年月日:220",
        "--allow-list", "更新", "000871", "CT-2024-000871",
    ])
    check(code == 0, "推奨コマンドが終了コード0", f"実際={code} {log.strip()[:120]}")
    if code != 0:
        for ok, label in checks:
            print(f"[{'OK ' if ok else 'NG!'}] {label}")
        return 1

    rep = json.loads(rep_p.read_text(encoding="utf-8"))
    check(not rep["verification"]["leaks"], "再OCR検証で残存なし")
    check(
        len(rep["ocr_passes"]) >= 2 and all(p["ocr_text_length"] > 100 for p in rep["ocr_passes"]),
        "複数OCRパスが機能",
        str([(p["psm"], p["upscale"], p["new_boxes"]) for p in rep["ocr_passes"]]),
    )
    check(
        any(d["entity_type"] == "LABEL_VALUE" for d in rep["detections"]),
        "--mask-right-of がボックスを生成",
    )
    check(
        not any(d["entity_type"] == "DATE_TIME" for d in rep["detections"]),
        "DATE_TIME 由来のボックスが無い",
    )

    before_i = Image.open(before_p).convert("RGB")
    after_i = Image.open(out_p).convert("RGB")

    for name, box in MUST_MASK:
        ink, unchanged, _ = ink_stats(before_i, after_i, box)
        check(ink > 0 and unchanged == 0, f"MASK {name}", f"インク{ink} 残存{unchanged}")
    for name, box in MUST_KEEP:
        ink, _, altered = ink_stats(before_i, after_i, box)
        check(ink > 0 and altered == 0, f"KEEP {name}", f"インク{ink} 改変{altered}")

    # 3. Opt-in financial profile: amounts and payment fields are masked
    # without changing the standard profile's behavior.
    fin_rep = tmp / "financial.json"
    fin_out = tmp / "financial.png"
    fin_code, _ = run([
        str(before_p), "-o", str(fin_out), "--report", str(fin_rep),
        "--profile", "financial",
    ])
    fin = json.loads(fin_rep.read_text(encoding="utf-8"))
    fin_types = {d["entity_type"] for d in fin["detections"]}
    check(fin_code == 0, "financialプロファイルが終了コード0", f"実際={fin_code}")
    check(
        {"JP_MONEY", "BANK_ACCOUNT"}.issubset(fin_types)
        and not fin["verification"]["leaks"],
        "financialプロファイルが金額・口座番号を検出して残存なし",
        f"types={sorted(fin_types)}",
    )

    # 4. Exit-code contracts.
    code, _ = run([str(clean_p), "-o", str(tmp / "clean_out.png")])
    check(code == 3, "PII不在の画像は終了コード3(未検証)", f"実際={code}")

    leak_rep = tmp / "leaky.json"
    code, _ = run([
        str(before_p), "-o", str(tmp / "leaky.png"),
        "--report", str(leak_rep), "--pad", "-12",
    ])
    leaks = json.loads(leak_rep.read_text(encoding="utf-8"))["verification"]["leaks"]
    check(code == 2 and bool(leaks), "塗り不足は終了コード2で検知", f"実際={code} 残存{len(leaks)}件")

    # 5. Verifier sanity: same detections, unmasked vs masked image.
    import types  # noqa: E402

    vargs = types.SimpleNamespace(lang="jpn+eng", psm="6")
    det = [m.Detection("JP_PHONE", "090-1234-5678", 0.6, 0, 0, 10, 10)]
    check(bool(m.verify(before_i, det, vargs)), "検証器は未マスク画像で残存を検知")
    check(not m.verify(after_i, det, vargs), "検証器はマスク済み画像で残存なし")

    # 6. Output must carry no EXIF/GPS.
    check(len(dict(Image.open(out_p).getexif())) == 0, "出力PNGにEXIFが残らない")

    ng = 0
    for ok, label in checks:
        if not ok:
            ng += 1
        print(f"[{'OK ' if ok else 'NG!'}] {label}")
    print(f"\n{len(checks)}項目中 {len(checks) - ng} 合格 / {ng} 不合格")
    if not a.keep and not a.workdir:
        print(f"作業ディレクトリ: {tmp}")
    return 0 if ng == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
